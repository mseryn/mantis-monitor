# Mantis-Monitor Setup Guide

Step-by-step instructions for installing Mantis-Monitor and configuring the
system permissions needed to run the **perf** and **BPF IO-latency**
collectors.

These steps assume:

* A Debian/Ubuntu-family Linux system (kernel ≥ 4.7).
* You have `sudo`.
* You will run Mantis from a Python virtual environment named `mvenv`.

> **Why so many permission steps?** Both collectors read low-level kernel
> telemetry. `perf` needs access to hardware performance counters; the BPF
> collector needs to load an eBPF program, attach it to syscall tracepoints,
> and read kernel tracefs metadata. Each of those is gated by a *different*
> kernel knob, so there is no single switch — you configure them one at a
> time below.

---

## 1. Download Mantis-Monitor

```bash
git clone https://github.com/mseryn/mantis-monitor.git
cd mantis-monitor
```

## 2. Create and populate the virtual environment

```bash
python3 -m venv mvenv
source mvenv/bin/activate
pip install --upgrade pip
pip install .          # or `pip install -e .` for an editable/dev install
```

After this you should have the `mantis-monitor` command on your PATH (while the
venv is active):

```bash
mantis-monitor --help
```

---

## 3. Run the perf collector test

The perf collector wraps `perf stat`. The only permission it needs is access
to hardware performance counters, controlled by
`kernel.perf_event_paranoid`.

### 3a. Check the current setting

```bash
cat /proc/sys/kernel/perf_event_paranoid
```

Values ≥ 1 block CPU performance-counter access. You want `-1` (or at least
`0`) for full hardware-counter collection.

### 3b. Lower it for the current boot

```bash
sudo sysctl -w kernel.perf_event_paranoid=-1
```

### 3c. Make it persistent across reboots

```bash
echo 'kernel.perf_event_paranoid = -1' | sudo tee /etc/sysctl.d/99-mantis-perf.conf
sudo sysctl --system
```

### 3d. Run the test

```bash
source mvenv/bin/activate
mantis-monitor tests/test_perf.yaml
```

You should get a `test_perf.csv` containing real time-series data for each
configured counter (cpu-cycles, instructions, cache-references, etc.).

> **Security note:** `perf_event_paranoid = -1` opens performance monitoring
> to all users. On a shared or production machine, prefer `0` (disallows only
> raw tracepoint access) or grant `CAP_PERFMON` to specific binaries instead.

---

## 4. Run the BPF IO-latency collector test

The BPF collector is more involved. It requires **four** separate things:

1. The **real** BCC Python bindings (from the system package, *not* PyPI).
2. The kernel to permit unprivileged BPF (`kernel.unprivileged_bpf_disabled`).
3. The Python interpreter to hold `CAP_BPF` + `CAP_PERFMON`.
4. Read access to the tracefs tracepoint metadata.

### 4a. Install the real BCC bindings

> ⚠️ **Do NOT `pip install bcc`.** The PyPI package named `bcc` is an unrelated
> "N-dimensional lattice" library and will not work. The genuine BPF Compiler
> Collection bindings link against the system `libbcc.so` and are only shipped
> as a distro package.

Install the system package (on Ubuntu/Debian it is `python3-bpfcc`):

```bash
sudo apt update
sudo apt install python3-bpfcc
```

This installs the bindings into the system Python at
`/usr/lib/python3/dist-packages/bcc`. Because they depend on the system
`libbcc.so`, the simplest way to use them from the venv is to symlink them in.
**Adjust `python3.12` to match your venv's Python version** (`ls mvenv/lib`):

```bash
# If a bogus PyPI 'bcc' was previously installed in the venv, remove it first:
pip uninstall -y bcc 2>/dev/null

ln -s /usr/lib/python3/dist-packages/bcc \
      mvenv/lib/python3.12/site-packages/bcc
```

Verify the import works:

```bash
source mvenv/bin/activate
python3 -c "from bcc import BPF; print('bcc OK')"
```

> If you prefer not to symlink, recreate the venv with
> `python3 -m venv --system-site-packages mvenv` so it can see the
> system-installed `bcc` directly.

### 4b. Allow unprivileged BPF

Check the current value:

```bash
cat /proc/sys/kernel/unprivileged_bpf_disabled
```

* `0` = unprivileged BPF allowed
* `1` = privileged only, but changeable at runtime
* `2` = privileged only, **locked** until reboot (cannot be lowered with
  `sysctl -w`)

If it is `2`, you must set it via config and **reboot** — a runtime
`sysctl -w` will be rejected. Set it persistently:

```bash
echo 'kernel.unprivileged_bpf_disabled = 0' | sudo tee /etc/sysctl.d/99-mantis-bpf.conf
sudo sysctl --system        # works if current value is 0 or 1
# If it was 2, reboot now for the change to take effect.
```

### 4c. Grant capabilities to the venv Python

Loading a BPF program and attaching it to tracepoints needs `CAP_BPF` and
`CAP_PERFMON`. Rather than running everything as root, grant those two
capabilities to the venv's Python interpreter.

The venv's `python3` is usually a symlink — `setcap` must be applied to the
**real** binary, so resolve it first:

```bash
REAL_PY=$(readlink -f mvenv/bin/python3)
sudo setcap cap_bpf,cap_perfmon+eip "$REAL_PY"

# Confirm:
getcap "$REAL_PY"
```

> **Notes & caveats:**
> * This grants the capabilities to *every* script run by that interpreter, so
>   only do it on a venv you control.
> * If you delete and recreate the venv, you must re-run `setcap`.
> * Alternatively, skip this step and just run the tool with `sudo`:
>   `sudo mvenv/bin/mantis-monitor tests/test_bpf_io_latency.yaml`.

### 4d. Open tracefs tracepoint metadata

BCC reads tracepoint IDs from `/sys/kernel/tracing`, which is `root`-only by
default. Grant read/traverse access:

```bash
sudo chmod -R o+rx /sys/kernel/tracing/
```

> **This does not survive a reboot** — tracefs is a virtual filesystem
> recreated on each boot. To make it persistent, either:
>
> * Remount it with a group you belong to via `/etc/fstab`:
>
>   ```
>   tracefs  /sys/kernel/tracing  tracefs  gid=<your-group>,mode=750  0  0
>   ```
>
> * Or re-apply the `chmod` from a boot script / systemd unit.

### 4e. Run the test

```bash
source mvenv/bin/activate
mantis-monitor tests/test_bpf_io_latency.yaml
```

You should get a `bpf_io_latency_test.csv` with per-second
`io_read_latency_ns`, `io_write_latency_ns`, and `io_combined_latency_ns`
time-series.

> **Harmless noise:** BCC compiles the eBPF program at runtime and prints a
> number of `clang` warnings (e.g. *"multiple identical address spaces"*,
> *"declaration … will not be visible"*) sourced from the kernel headers.
> These are expected and do not affect collection.
>
> **Seeing only `None` values?** That means no IO occurred during a monitored
> window. The collector samples once per second, so the benchmark must perform
> sustained IO for several seconds. Buffered writes to `/tmp` complete in the
> page cache almost instantly; use `oflag=dsync` (as the example test does) to
> force each block to disk and produce measurable latency over multiple
> windows.

---

## Permission summary cheat-sheet

| Need | Mechanism | Persistent? |
|------|-----------|-------------|
| perf hardware counters | `kernel.perf_event_paranoid = -1` | `/etc/sysctl.d/*.conf` |
| BCC Python bindings | `apt install python3-bpfcc` + symlink into venv | yes (re-symlink if venv recreated) |
| Load BPF programs | `kernel.unprivileged_bpf_disabled = 0` | `/etc/sysctl.d/*.conf` (reboot if locked at `2`) |
| Attach to tracepoints | `setcap cap_bpf,cap_perfmon+eip` on venv python | yes (re-run if venv recreated) |
| Read tracepoint metadata | `chmod o+rx /sys/kernel/tracing` | **no** — re-apply per boot |
