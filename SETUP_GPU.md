# Mantis-Monitor GPU Setup Guide

Step-by-step instructions for installing Mantis-Monitor and configuring the
two GPU collectors:

* **ROCm collector** (`rocm`) — AMD GPUs, via `rocm-smi`
* **NVIDIA collector** (`nvidia`) — NVIDIA GPUs, via `nvidia-smi`

This guide assumes you have `sudo`. For the CPU/perf/BPF collectors, see
[`SETUP.md`](SETUP.md) instead.

> Both GPU collectors shell out to the vendor's standard SMI tool, parse its
> output, and record per-GPU time-series while your benchmark runs. They do
> **not** need the eBPF / perf permission gymnastics from `SETUP.md` — the main
> requirement is that the vendor tool is installed and your user can query the
> GPU.

---

## 1. Download Mantis-Monitor and create the venv

```bash
git clone https://github.com/mseryn/mantis-monitor.git
cd mantis-monitor

python3 -m venv mvenv
source mvenv/bin/activate
pip install --upgrade pip
pip install .          # or `pip install -e .` for an editable/dev install
```

Confirm the CLI is available (with the venv active):

```bash
mantis-monitor --help
```

---

## 2. AMD GPUs — the ROCm collector

The ROCm collector polls `rocm-smi --json` once per `time_count` ms. You need
the ROCm stack installed and your user able to query the GPU.

### 2a. Install ROCm / `rocm-smi`

Follow AMD's official installer for your distro and kernel — it sets up the
`amdgpu` kernel driver plus the ROCm userspace. On Ubuntu the short version is:

```bash
# Add AMD's repo + key per https://rocm.docs.amd.com (version-specific), then:
sudo apt update
sudo apt install rocm-smi-lib        # provides the rocm-smi CLI
# (a full `sudo apt install rocm` pulls in the entire stack incl. HIP)
```

`rocm-smi` typically installs to `/opt/rocm/bin/rocm-smi`. Make sure it is on
`PATH` (ROCm installs usually drop a profile script):

```bash
export PATH=$PATH:/opt/rocm/bin      # add to ~/.bashrc to persist
which rocm-smi
```

> If you cannot or do not want to put it on `PATH`, set
> `collection_modes.rocm.rocm_smi_path` in your config to the absolute path
> (e.g. `/opt/rocm/bin/rocm-smi`).

### 2b. Grant your user access to the GPU

Querying the AMD GPU requires access to the `/dev/kfd` and `/dev/dri/*`
devices, which are owned by the `render` and `video` groups. Add yourself to
both, then log out and back in (or reboot) for it to take effect:

```bash
sudo usermod -aG render,video "$USER"
# log out / back in, then verify:
groups | tr ' ' '\n' | grep -E 'render|video'
```

### 2c. Verify rocm-smi works as your user

```bash
rocm-smi --showtemp --showpower --showuse --json
```

You should get a JSON object keyed by `card0`, `card1`, … If this prints valid
JSON without `sudo`, the collector will work.

### 2d. Run the ROCm test

```bash
source mvenv/bin/activate
mantis-monitor tests/test_rocm.yaml
```

This produces `test_rocm.csv` with per-GPU time-series
(`gpu_0_average_graphics_package_power_w`, `gpu_0_temperature_sensor_edge_c`,
`gpu_0_gpu_use`, …).

> **Seeing few or constant values?** The default benchmark just sleeps, so it
> samples an *idle* GPU. Edit the `cmd:` in `tests/test_rocm.yaml` to a real
> GPU workload (e.g. `rocm-bandwidth-test`, or your own HIP binary) running for
> at least a few seconds to see the numbers move. See the comments in that
> file.
>
> **`could not find 'rocm-smi'`?** It is not on `PATH` — either fix `PATH` (2a)
> or set `collection_modes.rocm.rocm_smi_path` to the absolute path.

---

## 3. NVIDIA GPUs — the NVIDIA collector

The NVIDIA collector uses `nvidia-smi`'s built-in streaming query mode.

### 3a. Install the driver / `nvidia-smi`

Install the NVIDIA driver for your distro (this provides `nvidia-smi`). On
Ubuntu:

```bash
sudo ubuntu-drivers autoinstall      # or install a specific nvidia-driver-NNN
# reboot if the driver was just installed
which nvidia-smi
```

### 3b. Verify nvidia-smi works as your user

```bash
nvidia-smi
nvidia-smi --query-gpu=timestamp,index,power.draw,utilization.gpu --format=csv
```

No special groups or `sudo` are required for these query modes — if the above
prints a table, the collector will work.

### 3c. (Optional) GPU tracing with Nsight Systems

The `nvidia` collector has an extra `gpu_trace` mode that captures detailed
kernel/API summaries via **Nsight Systems** (`nsys`). It is **disabled by
default** in `tests/test_nvidia.yaml`. To use it, install Nsight Systems and
add `gpu_trace` back to the `modes:` list:

```bash
which nsys      # install NVIDIA Nsight Systems if missing
```

`nsys` may require `kernel.perf_event_paranoid` to be lowered (see `SETUP.md`,
section 3) for full GPU-metrics capture.

### 3d. Run the NVIDIA test

```bash
source mvenv/bin/activate
mantis-monitor tests/test_nvidia.yaml
```

This produces `test_nvidia.csv` with per-GPU, per-mode time-series
(`gpu_0_power.draw`, `gpu_0_utilization.gpu`, `gpu_0_temperature.gpu`, …).

> Same idle-GPU caveat as the ROCm collector: swap the `cmd:` in
> `tests/test_nvidia.yaml` for a real GPU workload to see activity.

---

## Configuration reference

### `rocm` collector (`collection_modes.rocm`) — all keys optional

| Key | Meaning | Default |
|-----|---------|---------|
| `metrics` | List of case-insensitive substrings; keep only fields whose name matches one | *(all numeric fields)* |
| `flags` | rocm-smi query flags | `--showtemp --showpower --showuse --showmemuse --showclocks --showvoltage` |
| `rocm_smi_path` | Path/name of the rocm-smi binary | `rocm-smi` |

```yaml
collection_modes:
  rocm:
    metrics: [power, temperature, use]
    flags: [--showtemp, --showpower]
    rocm_smi_path: /opt/rocm/bin/rocm-smi
```

### `nvidia` collector (`collection_modes.nvidia`)

| Key | Meaning |
|-----|---------|
| `gen` | GPU SM/compute generation, recorded for provenance |
| `modes` | List of: `power_time`, `utilization_time`, `memory_basic_time`, `temperature_time`, `clocks_time`, `gpu_trace` (needs `nsys`) |

```yaml
collection_modes:
  nvidia:
    gen: 8
    modes: [power_time, utilization_time, temperature_time]
```

---

## Permission summary cheat-sheet

| GPU | Need | Mechanism |
|-----|------|-----------|
| AMD | `rocm-smi` installed + on PATH | ROCm install; `PATH` or `rocm_smi_path` config |
| AMD | Query the GPU as your user | `usermod -aG render,video $USER` (re-login) |
| NVIDIA | `nvidia-smi` installed | NVIDIA driver install |
| NVIDIA | SMI query modes | none (works as normal user) |
| NVIDIA | `gpu_trace` mode | install `nsys`; may need `perf_event_paranoid` lowered |
