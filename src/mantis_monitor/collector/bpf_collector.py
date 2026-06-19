# This file is part of the Mantis-Monitor data collection suite.
# Mantis, including the data collection suite (mantis-monitor) and is

# Mantis is free software:
# you can redistribute it and/or modify it under the terms of the GNU Lesser
# General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# Mantis is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with Mantis. If not, see <https://www.gnu.org/licenses/>.

"""
This file contains the implementation of the BPF Collector.

The BPF Collector launches the target benchmark, discovers its PID (and all
descendant PIDs), attaches eBPF tracepoints to the running process tree, and
samples the collected metrics once per second for the duration of the run.

Currently supported metrics (select via the ``metrics`` key in the config):

    - ``io_latency`` — per-second average read latency, write latency, and
      combined read+write latency, all in nanoseconds.  Values are measured
      at the Linux syscall boundary (``read``/``write`` syscalls), so they
      capture time spent waiting in the kernel including filesystem, network,
      and block-device stacks.

Example ``config.yaml`` entry::

    collection_modes:
      bpf:
        metrics:
          - io_latency

Runtime requirements:
    - Python ``bcc`` package (BPF Compiler Collection).  On Debian/Ubuntu:
      ``sudo apt install python3-bcc``.  On RHEL/Fedora: ``sudo dnf install
      python3-bcc``.  See also https://github.com/iovisor/bcc.
    - Linux kernel ≥ 4.7 (``sys_enter/exit_read`` and
      ``sys_enter/exit_write`` tracepoints).
    - ``CAP_BPF`` + ``CAP_PERFMON`` capabilities, or run as root.
    - ``python3-psutil`` (already a mantis-monitor dependency).

.. note::

   For each newly-created Collector(), register_collector() must be called,
   and the file must be added to ``__init__.py``.

.. note::

   Only ``read(2)`` and ``write(2)`` syscalls are instrumented in this first
   version.  Future work can extend coverage to ``pread64``, ``pwrite64``,
   ``readv``, ``writev``, ``preadv``, ``pwritev``, and io_uring operations.
"""

import asyncio
import ctypes
import time
import os

import psutil

try:
    from bcc import BPF as _BCC_BPF
    _HAS_BCC = True
except ImportError:          # pragma: no cover
    _BCC_BPF = None
    _HAS_BCC = False

from mantis_monitor.collector.collector import Collector


# ──────────────────────────────────────────────────────────────────────────────
# BPF C program — IO latency via syscall tracepoints
# ──────────────────────────────────────────────────────────────────────────────

_BPF_IO_LATENCY_PROG = r"""
#include <linux/ptrace.h>

/*
 * Dynamic set of TGIDs (Linux "process IDs" as seen from userspace) whose
 * IO syscalls we want to measure.  Updated from Python every second to
 * include newly-spawned children of the benchmark process.
 *
 * Key:   TGID (u32)
 * Value: 1 (u8, presence flag)
 */
BPF_HASH(traced_pids, u32, u8, 1024);

/*
 * Per-thread in-flight start timestamps.  Keyed by TID (the kernel-level
 * thread ID, lower 32 bits of bpf_get_current_pid_tgid()) so that
 * concurrent threads in the same process each track their own syscall.
 */
BPF_HASH(read_start,  u32, u64);
BPF_HASH(write_start, u32, u64);

/*
 * Accumulated statistics for the current 1-second measurement interval.
 * Python resets these to zero after each snapshot.
 *
 * Index  Meaning
 * -----  -------
 *   0    read_count      — number of completed read() syscalls
 *   1    read_total_ns   — sum of their latencies (nanoseconds)
 *   2    write_count     — number of completed write() syscalls
 *   3    write_total_ns  — sum of their latencies (nanoseconds)
 */
BPF_ARRAY(io_stats, u64, 4);

/* Return non-zero if the current thread's TGID is in our watch set. */
static __always_inline int pid_traced(void)
{
    u32 tgid = (u32)(bpf_get_current_pid_tgid() >> 32);
    return traced_pids.lookup(&tgid) != NULL;
}

/* ── read() entry ──────────────────────────────────────────────────────── */

TRACEPOINT_PROBE(syscalls, sys_enter_read)
{
    if (!pid_traced()) return 0;
    u32 tid = (u32)bpf_get_current_pid_tgid();
    u64 ts  = bpf_ktime_get_ns();
    read_start.update(&tid, &ts);
    return 0;
}

/* ── read() exit ───────────────────────────────────────────────────────── */

TRACEPOINT_PROBE(syscalls, sys_exit_read)
{
    if (!pid_traced()) return 0;
    u32 tid  = (u32)bpf_get_current_pid_tgid();
    u64 *tsp = read_start.lookup(&tid);
    if (!tsp) return 0;                    /* no matching entry() — skip   */
    u64 delta = bpf_ktime_get_ns() - *tsp;
    read_start.delete(&tid);

    u32 k0 = 0, k1 = 1;
    u64 *cnt = io_stats.lookup(&k0);  if (cnt) lock_xadd(cnt, 1);
    u64 *tot = io_stats.lookup(&k1);  if (tot) lock_xadd(tot, delta);
    return 0;
}

/* ── write() entry ─────────────────────────────────────────────────────── */

TRACEPOINT_PROBE(syscalls, sys_enter_write)
{
    if (!pid_traced()) return 0;
    u32 tid = (u32)bpf_get_current_pid_tgid();
    u64 ts  = bpf_ktime_get_ns();
    write_start.update(&tid, &ts);
    return 0;
}

/* ── write() exit ──────────────────────────────────────────────────────── */

TRACEPOINT_PROBE(syscalls, sys_exit_write)
{
    if (!pid_traced()) return 0;
    u32 tid  = (u32)bpf_get_current_pid_tgid();
    u64 *tsp = write_start.lookup(&tid);
    if (!tsp) return 0;
    u64 delta = bpf_ktime_get_ns() - *tsp;
    write_start.delete(&tid);

    u32 k2 = 2, k3 = 3;
    u64 *cnt = io_stats.lookup(&k2);  if (cnt) lock_xadd(cnt, 1);
    u64 *tot = io_stats.lookup(&k3);  if (tot) lock_xadd(tot, delta);
    return 0;
}
"""


# ──────────────────────────────────────────────────────────────────────────────
# Collector
# ──────────────────────────────────────────────────────────────────────────────

class BPFCollector(Collector):
    """
    Collector that attaches eBPF tracepoints to the benchmark process tree and
    gathers runtime metrics that are not accessible through perf or psutil.

    Configured via the ``bpf`` key in ``collection_modes``::

        collection_modes:
          bpf:
            metrics:
              - io_latency   # read/write syscall latency averaged each second

    If ``metrics`` is omitted it defaults to ``["io_latency"]``.

    :ivar name: BPFCollector
    :ivar description: Describes this collector
    :ivar benchmark: Benchmark class this Collector is initiated against
    :ivar benchmark_set: Colon-separated list of co-running benchmarks
    :ivar iteration: The statistical or experimental iteration
    :ivar metrics: List of BPF metric names to collect
    :ivar timescale: Sampling interval in ms (from Configuration; informational
        only — the BPF metrics are always sampled at 1-second intervals)
    :ivar testruns: List of TestRun objects, one per requested metric
    :ivar data: Collected data in the UDF format
    """

    def __init__(self, configuration, iteration, benchmark, benchmark_set):
        """
        Init the object and call setup().

        :param configuration: Configuration object from this mantis-monitor instance
        :type configuration: Configuration()
        :param iteration: The current experimental iteration
        :type iteration: int
        :param benchmark: Benchmark class this Collector is initiated against
        :type benchmark: Benchmark()
        :param benchmark_set: Colon-separated list of co-running benchmarks
        :type benchmark_set: str
        :return: None
        """
        self.name        = "BPFCollector"
        self.description = "Collector for eBPF-based runtime metric collection"
        self.benchmark     = benchmark
        self.benchmark_set = benchmark_set
        self.iteration     = iteration
        self.timescale     = configuration.timescale
        self.testruns      = []
        self.data          = []

        bpf_config = configuration.collector_modes.get("bpf") or {}
        if isinstance(bpf_config, dict) and "metrics" in bpf_config:
            self.metrics = list(bpf_config["metrics"])
        else:
            self.metrics = ["io_latency"]

        self.setup()

    def setup(self):
        """
        Create one TestRun instance per requested metric.

        Unknown metric names are skipped with a warning printed to stdout.

        :return: None
        """
        for metric in self.metrics:
            if metric == "io_latency":
                self.testruns.append(
                    BPFIOLatencyTestRun(
                        name          = "{}_io_latency".format(self.name),
                        benchmark     = self.benchmark,
                        iteration     = self.iteration,
                        benchmark_set = self.benchmark_set,
                    )
                )
            else:
                print(
                    "[BPFCollector] Unknown metric '{}' — skipping. "
                    "Supported metrics: io_latency".format(metric)
                )

    async def run_all(self):
        """
        Run all BPF TestRun instances sequentially and yield after each one.

        :return: None, yielded for each invocation of the Benchmark associated
            with this Collector instance
        """
        for testrun in self.testruns:
            testrun.benchmark.before_each()
            data = await testrun.run()
            testrun.benchmark.after_each()
            self.data.append(data)
            yield


# ──────────────────────────────────────────────────────────────────────────────
# IO latency TestRun
# ──────────────────────────────────────────────────────────────────────────────

class BPFIOLatencyTestRun:
    """
    Runs the benchmark with ``sys_enter/exit_read`` and ``sys_enter/exit_write``
    tracepoints attached and produces three per-second time-series:

    ``io_read_latency_ns``
        Average latency (ns) of ``read(2)`` syscalls that completed during
        each 1-second window.  ``None`` when no reads occurred that second.

    ``io_write_latency_ns``
        Average latency (ns) of ``write(2)`` syscalls that completed during
        each 1-second window.  ``None`` when no writes occurred that second.

    ``io_combined_latency_ns``
        Average latency (ns) across all IO (reads + writes) that completed
        during each 1-second window.  ``None`` when no IO occurred.

    Latency is measured from the tracepoint at the syscall entry to the
    tracepoint at the syscall exit, so it includes time waiting in the
    kernel (buffer cache misses, disk seeks, network round-trips, etc.)
    but not userspace overhead.

    The BPF program filters events by TGID so only the benchmark process tree
    (the launched process and all its descendants) is measured.  The watched
    TGID set is refreshed every second via psutil so newly-forked children are
    picked up quickly.

    The format of stored data (in the returned dictionary):

    .. code-block:: python

        {
          "benchmark_name":          str,
          "benchmark_set":           str,
          "collector_name":          str,
          "iteration":               int,
          "timescale":               1000,   # ms — always 1-second windows
          "units":                   "nanoseconds (average per 1-second interval)",
          "measurements":            ["io_read_latency_ns",
                                      "io_write_latency_ns",
                                      "io_combined_latency_ns"],
          "io_read_latency_ns":      [[time_s, value_or_None], ...],
          "io_write_latency_ns":     [[time_s, value_or_None], ...],
          "io_combined_latency_ns":  [[time_s, value_or_None], ...],
          "duration":                float,  # total runtime in seconds
        }

    :ivar name: Unique name for this TestRun
    :ivar benchmark: Associated Benchmark object
    :ivar benchmark_set: Colon-separated co-running benchmark names
    :ivar iteration: Experimental iteration number
    :ivar data: Final UDF-format result dictionary
    """

    #: The three metric keys emitted into ``data``.
    METRIC_KEYS = (
        "io_read_latency_ns",
        "io_write_latency_ns",
        "io_combined_latency_ns",
    )

    def __init__(self, name, benchmark, iteration, benchmark_set):
        """
        Init this BPFIOLatencyTestRun.

        :param name: Unique name for this TestRun
        :type name: str
        :param benchmark: Associated Benchmark object
        :type benchmark: Benchmark()
        :param iteration: Experimental iteration number
        :type iteration: int
        :param benchmark_set: Colon-separated co-running benchmark names
        :type benchmark_set: str
        :return: None
        """
        self.name          = name
        self.benchmark     = benchmark
        self.benchmark_set = benchmark_set
        self.iteration     = iteration

        self.data = {
            "benchmark_name": self.benchmark.name,
            "benchmark_set":  self.benchmark_set,
            "collector_name": self.name,
            "iteration":      self.iteration,
            "timescale":      1000,   # always 1-second windows
            "units":          "nanoseconds (average per 1-second interval)",
            "measurements":   list(self.METRIC_KEYS),
            "duration":       0.0,
        }
        for key in self.METRIC_KEYS:
            self.data[key] = []

    # ── private helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _update_traced_pids(shell_proc, traced_pids_map):
        """
        Refresh the ``traced_pids`` BPF map with every live TGID in the
        benchmark's process tree (the shell and all its descendants).

        New child processes that were spawned since the last call are added;
        already-present entries are left in place (harmless duplication is
        fine — the map is bounded at 1 024 entries which is more than enough
        for any realistic benchmark).

        :param shell_proc: ``psutil.Process`` for the top-level shell started
            by ``asyncio.create_subprocess_shell``
        :type shell_proc: psutil.Process
        :param traced_pids_map: BCC table object for the ``traced_pids`` map
        :return: None
        """
        live_pids = set()
        try:
            live_pids.add(shell_proc.pid)
            for child in shell_proc.children(recursive=True):
                live_pids.add(child.pid)
        except psutil.NoSuchProcess:
            pass   # process just exited — work with whatever we collected

        for pid in live_pids:
            key = ctypes.c_uint32(pid)
            try:
                traced_pids_map[key] = traced_pids_map.Leaf(1)
            except Exception:
                try:
                    # Fallback for BCC versions with different Leaf semantics
                    traced_pids_map[key] = ctypes.c_uint8(1)
                except Exception:
                    pass   # best-effort; missing a PID means we lose that data

    @staticmethod
    def _snapshot_and_reset(io_stats_map):
        """
        Read the four counters from the ``io_stats`` BPF array and
        immediately reset them to zero for the next interval.

        There is an inherent race between reading and zeroing: events that
        arrive in that tiny window are attributed to the *next* interval.
        For 1-second averages this inaccuracy is negligible.

        :param io_stats_map: BCC table object for the ``io_stats`` array
        :returns: dict with keys ``read_count``, ``read_total_ns``,
            ``write_count``, ``write_total_ns``
        :rtype: dict
        """
        result = {"read_count": 0, "read_total_ns": 0,
                  "write_count": 0, "write_total_ns": 0}
        names = list(result.keys())   # order matches array indices 0-3

        for idx, field in enumerate(names):
            try:
                result[field] = io_stats_map[ctypes.c_int(idx)].value
            except Exception:
                result[field] = 0

        # Zero the counters — best-effort with two fallback strategies.
        try:
            zero_leaf = io_stats_map.Leaf(0)
            for idx in range(4):
                io_stats_map[ctypes.c_int(idx)] = zero_leaf
        except Exception:
            for idx in range(4):
                try:
                    entry = io_stats_map[ctypes.c_int(idx)]
                    entry.value = 0
                    io_stats_map[ctypes.c_int(idx)] = entry
                except Exception:
                    pass

        return result

    @staticmethod
    def _compute_averages(stats):
        """
        Derive per-second average latencies from a raw stats snapshot.

        :param stats: dict as returned by :meth:`_snapshot_and_reset`
        :type stats: dict
        :returns: ``(read_avg_ns, write_avg_ns, combined_avg_ns)`` — each
            element is either a ``float`` (ns) or ``None`` if no operations
            of that type were observed this interval.
        :rtype: tuple
        """
        rc = stats["read_count"]
        rt = stats["read_total_ns"]
        wc = stats["write_count"]
        wt = stats["write_total_ns"]

        read_avg     = (rt / rc)            if rc > 0           else None
        write_avg    = (wt / wc)            if wc > 0           else None
        total_count  = rc + wc
        combined_avg = ((rt + wt) / total_count) if total_count > 0 else None

        return read_avg, write_avg, combined_avg

    # ── main entry point ─────────────────────────────────────────────────────

    async def run(self):
        """
        Load the BPF program, start the benchmark, collect per-second
        average IO latency until the benchmark exits, then return the
        accumulated data dictionary.

        Flow:

        1. Compile and load the eBPF program (takes ~0.5 s on first run due
           to LLVM compilation).
        2. Launch the benchmark via ``asyncio.create_subprocess_shell``.
        3. Seed ``traced_pids`` with the shell's PID; yield briefly so the
           shell can ``exec`` the target binary and populate children.
        4. Monitoring loop — every second:
           a. Refresh ``traced_pids`` with new child PIDs (psutil).
           b. Snapshot and zero ``io_stats``.
           c. Compute averages and append ``[timestamp, value]`` to data.
        5. Wait for the subprocess to exit, record total duration.

        :return: Populated ``self.data`` dictionary
        :rtype: dict
        :raises RuntimeError: if the ``bcc`` package is not installed
        """
        if not _HAS_BCC:
            raise RuntimeError(
                "BPFIOLatencyTestRun requires the 'bcc' Python package.\n"
                "  Debian/Ubuntu: sudo apt install python3-bcc\n"
                "  RHEL/Fedora:   sudo dnf install python3-bcc\n"
                "  Source:        https://github.com/iovisor/bcc"
            )

        # ── 1. Compile and load BPF program ─────────────────────────────────
        bpf = _BCC_BPF(text=_BPF_IO_LATENCY_PROG)
        traced_pids_map = bpf["traced_pids"]
        io_stats_map    = bpf["io_stats"]

        # ── 2. Launch the benchmark ──────────────────────────────────────────
        start_time = time.time()
        process = await asyncio.create_subprocess_shell(
            self.benchmark.get_run_command(),
            cwd = self.benchmark.cwd,
            env = self.benchmark.env,
        )

        # ── 3. Seed the PID set and let the shell exec the target ────────────
        try:
            shell_proc = psutil.Process(process.pid)
            self._update_traced_pids(shell_proc, traced_pids_map)
        except psutil.NoSuchProcess:
            shell_proc = None

        await asyncio.sleep(0.1)   # let the shell exec the target binary

        if shell_proc is not None:
            try:
                self._update_traced_pids(shell_proc, traced_pids_map)
            except psutil.NoSuchProcess:
                pass

        # ── 4. Monitoring loop (1-second intervals) ──────────────────────────
        while shell_proc is not None and shell_proc.is_running():
            await asyncio.sleep(1.0)

            timestamp = time.time() - start_time

            # Refresh child PID set before snapshotting, so any children that
            # spawned during the last second are included.
            try:
                self._update_traced_pids(shell_proc, traced_pids_map)
            except psutil.NoSuchProcess:
                pass

            # Snapshot and reset BPF counters for this interval
            stats = self._snapshot_and_reset(io_stats_map)
            read_avg, write_avg, combined_avg = self._compute_averages(stats)

            self.data["io_read_latency_ns"].append([timestamp, read_avg])
            self.data["io_write_latency_ns"].append([timestamp, write_avg])
            self.data["io_combined_latency_ns"].append([timestamp, combined_avg])

        # ── 5. Wait for process exit and record duration ─────────────────────
        await process.wait()
        self.data["duration"] = time.time() - start_time

        return self.data


Collector.register_collector("bpf", BPFCollector)
