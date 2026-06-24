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
This file contains the implementation of the ROCm SMI Collector.

The ROCm SMI Collector samples AMD GPU telemetry using ``rocm-smi`` — the
standard system-management tool shipped with the ROCm stack on AMD GPUs.

Unlike ``nvidia-smi`` (which has a built-in ``--loop-ms`` sampling mode) and
``amd-smi`` (which has a ``monitor -w`` mode), ``rocm-smi`` has no native
"watch over time" mode.  This collector therefore launches the benchmark as a
subprocess and *polls* ``rocm-smi --json`` once per ``time_count`` milliseconds
for the lifetime of the benchmark, timestamping each sample itself.

Currently collected (per GPU, one time-series per field, default flag set):

    - temperature  (``--showtemp``)    — edge / junction / memory sensors, °C
    - power        (``--showpower``)   — average graphics package power, W
    - GPU use      (``--showuse``)     — busy percentage
    - memory use   (``--showmemuse``)  — VRAM / GTT busy percentage
    - clocks       (``--showclocks``)  — sclk / mclk / fclk, MHz
    - voltage      (``--showvoltage``) — GPU voltage, mV

Because ``rocm-smi`` JSON field names differ across ROCm releases, this
collector does not hard-code a field list.  It parses every numeric field
``rocm-smi`` returns and emits it as ``gpu_<index>_<sanitized_field_name>``.
An optional ``metrics`` filter (list of case-insensitive substrings) can be
supplied to keep only matching fields.

Example ``config.yaml`` entry::

    collection_modes:
      rocm:
        # all keys below are OPTIONAL
        metrics:                 # keep only fields whose name matches one of
          - power                #   these substrings (omit to keep everything)
          - temperature
          - use
        flags:                   # override the rocm-smi query flags
          - --showtemp
          - --showpower
          - --showuse
        rocm_smi_path: rocm-smi  # path/name of the rocm-smi binary

Runtime requirements:
    - AMD GPU with the ROCm stack installed and ``rocm-smi`` on ``PATH``
      (see SETUP_GPU.md).
    - ``python3-psutil`` (already a mantis-monitor dependency) — used to detect
      when the benchmark process tree has exited.

.. note::

   For each newly-created Collector(), register_collector() must be called,
   and the file must be added to ``__init__.py``.

.. note::

   Like the nvidia and amd-smi collectors, sampling is currently *system-wide*
   (it reports whole-GPU telemetry, not per-process).  Co-running unrelated GPU
   work will be reflected in the readings.
"""

import asyncio
import json
import os
import re
import time

import psutil

from mantis_monitor.collector.collector import Collector


# ──────────────────────────────────────────────────────────────────────────────
# Parsing helpers (module-level so they are unit-testable without a GPU)
# ──────────────────────────────────────────────────────────────────────────────

#: Default rocm-smi query flags.  Chosen to return mostly-numeric, broadly
#: available telemetry.  Override via ``collection_modes.rocm.flags``.
DEFAULT_ROCM_SMI_FLAGS = [
    "--showtemp",
    "--showpower",
    "--showuse",
    "--showmemuse",
    "--showclocks",
    "--showvoltage",
]

_NUMBER_RE = re.compile(r"[-+]?\d*\.?\d+")


def parse_numeric(raw):
    """
    Extract the first numeric value from a rocm-smi field value.

    rocm-smi values arrive as strings and sometimes carry inline units or
    decoration, e.g. ``"35.0"``, ``"(300Mhz)"``, ``"806"``, ``"N/A"``.  This
    pulls out the leading number and returns it as a float, or ``None`` if the
    value holds no usable number (``"N/A"``, empty, pure text).

    :param raw: the raw rocm-smi value (usually ``str``)
    :returns: ``float`` or ``None``
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if text == "" or text.upper() == "N/A":
        return None
    match = _NUMBER_RE.search(text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def sanitize_key(raw):
    """
    Turn a rocm-smi field label into a CSV/column-friendly metric name.

    e.g. ``"Average Graphics Package Power (W)"`` ->
    ``"average_graphics_package_power_w"``.

    :param raw: the raw rocm-smi field label
    :returns: lowercase, ``_``-separated, alphanumeric key
    """
    key = str(raw).strip().lower()
    key = re.sub(r"[^a-z0-9]+", "_", key)
    return key.strip("_")


def card_index(card_name):
    """
    Derive a GPU index from a rocm-smi top-level key such as ``"card0"``.

    :param card_name: the rocm-smi card key (e.g. ``"card0"``)
    :returns: the numeric index as a string (``"0"``), or the original name if
        no digits are present.
    """
    match = re.search(r"(\d+)", str(card_name))
    return match.group(1) if match else str(card_name)


def parse_rocm_smi_json(payload, metrics_filter=None):
    """
    Flatten one ``rocm-smi --json`` payload into ``{metric_key: value}``.

    :param payload: the decoded JSON dict (``{"card0": {field: value, ...}}``)
    :param metrics_filter: optional iterable of lowercase substrings; if given,
        only metrics whose sanitized name contains one of them are kept.
    :returns: dict mapping ``gpu_<index>_<field>`` -> float
    """
    flattened = {}
    if not isinstance(payload, dict):
        return flattened
    for card_name, fields in payload.items():
        if not isinstance(fields, dict):
            continue
        index = card_index(card_name)
        for raw_key, raw_value in fields.items():
            value = parse_numeric(raw_value)
            if value is None:
                continue
            metric = sanitize_key(raw_key)
            if metrics_filter and not any(f in metric for f in metrics_filter):
                continue
            flattened["gpu_{index}_{metric}".format(index=index, metric=metric)] = value
    return flattened


# ──────────────────────────────────────────────────────────────────────────────
# Collector
# ──────────────────────────────────────────────────────────────────────────────

class ROCmSMICollector(Collector):
    """
    This is the implementation of the ROCm SMI Collector.

    It inherits directly from the Collector() class and samples AMD GPU
    telemetry by polling ``rocm-smi --json`` while the benchmark runs.

    Configured via the ``rocm`` key in ``collection_modes`` (all sub-keys
    optional)::

        collection_modes:
          rocm:
            metrics:                 # keep only matching fields (substrings)
              - power
              - temperature
            flags:                   # override rocm-smi query flags
              - --showtemp
              - --showpower
            rocm_smi_path: rocm-smi  # path to the rocm-smi binary

    :ivar name: ROCmSMICollector
    :ivar description: Describes this collector
    :ivar benchmark: Benchmark class this Collector is initiated against
    :ivar benchmark_set: Colon-separated list of co-running benchmarks
    :ivar iteration: The statistical or experimental iteration
    :ivar timescale: The time between collections in MS, from Configuration()
    :ivar metrics_filter: Optional list of substrings to restrict fields
    :ivar flags: rocm-smi query flags
    :ivar rocm_smi_path: Path/name of the rocm-smi binary
    :ivar testruns: List of TestRun() instances to run against this Collector
    :ivar data: Data from this Collector instance stored in the UDF
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
        self.name = "ROCmSMICollector"
        self.description = "Collector for AMD GPU telemetry via rocm-smi"
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration
        self.timescale = configuration.timescale  # ms, same as config file
        self.testruns = []
        self.data = []

        rocm_config = configuration.collector_modes.get("rocm") or {}
        if not isinstance(rocm_config, dict):
            rocm_config = {}

        metrics_filter = rocm_config.get("metrics")
        if metrics_filter:
            self.metrics_filter = [str(m).strip().lower() for m in metrics_filter]
        else:
            self.metrics_filter = None

        self.flags = list(rocm_config.get("flags") or DEFAULT_ROCM_SMI_FLAGS)
        self.rocm_smi_path = rocm_config.get("rocm_smi_path", "rocm-smi")

        self.setup()

    def setup(self):
        """
        Create the single over-time TestRun for this collector.

        :return: None
        """
        self.testruns.append(
            ROCmSMIOverTimeTestRun(
                name           = "ROCmSMIOverTime",
                benchmark      = self.benchmark,
                iteration      = self.iteration,
                timescale      = self.timescale,
                benchmark_set  = self.benchmark_set,
                flags          = self.flags,
                rocm_smi_path  = self.rocm_smi_path,
                metrics_filter = self.metrics_filter,
            )
        )

    async def run_all(self):
        """
        Runs all TestRun() instances for this Benchmark()

        :return: None, yielded for each invocation of the Benchmark associated
            with this Collector instance
        """
        for this_testrun in self.testruns:
            this_testrun.benchmark.before_each()
            data = await this_testrun.run()
            this_testrun.benchmark.after_each()
            if isinstance(data, list):
                self.data.extend(data)
            else:
                self.data.append(data)
            yield


# ──────────────────────────────────────────────────────────────────────────────
# Over-time TestRun
# ──────────────────────────────────────────────────────────────────────────────

class ROCmSMIOverTimeTestRun():
    """
    Encapsulates polling ``rocm-smi`` over the lifetime of one benchmark run.

    The benchmark is launched as a subprocess; while it is alive, ``rocm-smi
    --json`` is invoked every ``timescale`` ms and each numeric field is
    appended to a per-field ``[timestamp_s, value]`` time-series.

    :ivar name: This TestRun()'s unique name
    :ivar benchmark: Benchmark class this Collector is initiated against
    :ivar benchmark_set: Colon-separated list of co-running benchmarks
    :ivar iteration: The statistical or experimental iteration
    :ivar timescale: The time between collections in MS, from Configuration()
    :ivar flags: rocm-smi query flags
    :ivar rocm_smi_path: Path/name of the rocm-smi binary
    :ivar metrics_filter: Optional list of substrings to restrict fields
    :ivar rows: Raw per-sample dicts collected during the run
    :ivar data: The pivoted UDF-format result dictionary
    :ivar duration: The duration which the benchmark ran for

    The format of stored data (in the returned dictionary)::

        {
          "benchmark_name": str,
          "benchmark_set":  str,
          "collector_name": str,
          "iteration":      int,
          "timescale":      int,
          "units":          "time, value (units per rocm-smi field label)",
          "measurements":   ["gpu_0_average_graphics_package_power_w", ...],
          "gpu_0_average_graphics_package_power_w": [[t, value], ...],
          ...
          "duration":       float,
        }
    """

    def __init__(self, name, benchmark, iteration, timescale, benchmark_set,
                 flags, rocm_smi_path, metrics_filter):
        """
        Init this TestRun().

        :param name: This TestRun()'s unique name
        :param benchmark: Benchmark class this Collector is initiated against
        :param iteration: The statistical or experimental iteration
        :param timescale: The time between collections in MS, from Configuration()
        :param benchmark_set: Colon-separated list of co-running benchmarks
        :param flags: rocm-smi query flags (list of str)
        :param rocm_smi_path: Path/name of the rocm-smi binary
        :param metrics_filter: Optional list of lowercase substrings to keep

        :return: None
        """
        self.name = name
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration
        self.timescale = timescale
        self.flags = flags
        self.rocm_smi_path = rocm_smi_path
        self.metrics_filter = metrics_filter
        self.rows = []
        self.duration = 0

        self.data = {
            "benchmark_name": self.benchmark.name,
            "benchmark_set":  self.benchmark_set,
            "collector_name": self.name,
            "iteration":      self.iteration,
            "timescale":      self.timescale,
            "units":          "time, value (units per rocm-smi field label)",
            "measurements":   [],
            "duration":       self.duration,
        }

    async def _sample(self, timestamp):
        """
        Run ``rocm-smi --json`` once and record a single timestamped sample.

        Malformed or empty output is skipped (best-effort), but a missing
        ``rocm-smi`` binary raises so the failure is loud and obvious.

        :param timestamp: seconds since the benchmark started
        :raises RuntimeError: if the rocm-smi binary cannot be found
        :return: None
        """
        cmd = [self.rocm_smi_path] + list(self.flags) + ["--json"]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await proc.communicate()
        except FileNotFoundError:
            raise RuntimeError(
                "ROCmSMIOverTimeTestRun could not find '{}'.\n"
                "  Install the ROCm stack and ensure rocm-smi is on PATH, or set\n"
                "  collection_modes.rocm.rocm_smi_path in your config.\n"
                "  See SETUP_GPU.md for installation instructions.".format(self.rocm_smi_path)
            )

        try:
            payload = json.loads(stdout.decode("utf-8", "replace"))
        except (ValueError, json.JSONDecodeError):
            return  # transient/garbled output — skip this interval

        flattened = parse_rocm_smi_json(payload, self.metrics_filter)
        if flattened:
            flattened["time"] = timestamp
            self.rows.append(flattened)

    def _pivot(self):
        """
        Pivot the collected per-sample rows into per-field time-series in
        ``self.data`` and populate the ``measurements`` list.

        :return: None
        """
        for row in self.rows:
            t = row["time"]
            for key, value in row.items():
                if key == "time":
                    continue
                if key not in self.data:
                    self.data[key] = []
                    self.data["measurements"].append(key)
                self.data[key].append([t, value])

    async def run(self):
        """
        Launch the benchmark and poll rocm-smi until it exits.

        Flow:

        1. Launch the benchmark via ``asyncio.create_subprocess_shell``.
        2. Take an immediate baseline sample.
        3. Every ``timescale`` ms, while the benchmark process tree is alive,
           take another sample.
        4. Reap the benchmark, record total duration, pivot, and return.

        :return: Populated ``self.data`` dictionary
        :rtype: dict
        """
        interval = max(self.timescale / 1000.0, 0.1)

        start_time = time.time()
        print('Running command ' + self.benchmark.get_run_command())
        process = await asyncio.create_subprocess_shell(
            self.benchmark.get_run_command(),
            cwd=self.benchmark.cwd,
            env=self.benchmark.env,
        )

        try:
            shell_proc = psutil.Process(process.pid)
        except psutil.NoSuchProcess:
            shell_proc = None

        # Immediate baseline sample so even sub-interval benchmarks yield data.
        await self._sample(time.time() - start_time)

        while shell_proc is not None and shell_proc.is_running():
            await asyncio.sleep(interval)
            try:
                if not shell_proc.is_running():
                    break
            except psutil.NoSuchProcess:
                break
            await self._sample(time.time() - start_time)

        await process.wait()
        self.duration = time.time() - start_time
        self.data["duration"] = self.duration

        self._pivot()
        return self.data


Collector.register_collector("rocm", ROCmSMICollector)
