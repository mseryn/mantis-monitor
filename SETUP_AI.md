# Mantis-Monitor AI Benchmark Setup Guide

Install/build instructions for the three AI benchmark engines wired up as
mantis-monitor example configs, with CPU / NVIDIA / AMD variants for each:

| Engine | CPU | NVIDIA | AMD |
|--------|-----|--------|-----|
| **llama.cpp** (LLM inference) | `test_ai_llamacpp_cpu.yaml` | `test_ai_llamacpp_nvidia.yaml` | `test_ai_llamacpp_amd.yaml` |
| **ONNX Runtime** (CV/NLP inference) | `test_ai_onnx_cpu.yaml` | `test_ai_onnx_nvidia.yaml` | `test_ai_onnx_amd.yaml` |
| **MLPerf Inference** (MLCommons) | `test_ai_mlperf_cpu.yaml` | `test_ai_mlperf_nvidia.yaml` | `test_ai_mlperf_amd.yaml` |

All nine configs collect with **perf + BPF (io_latency) + pfs (utilization)**;
the NVIDIA variants add the **nvidia** collector and the AMD variants add the
**rocm** collector.

## Prerequisites — read these first

* **Collector permissions.** These configs use perf, BPF, and the pfs
  collector. Set those up per [`SETUP.md`](SETUP.md) (perf_event_paranoid,
  unprivileged BPF, capabilities, tracefs). The GPU variants additionally need
  the GPU tool setup in [`SETUP_GPU.md`](SETUP_GPU.md).
* **Run from the repo root.** mantis-monitor launches the benchmark with the
  working directory it was started in, and all the example commands use paths
  relative to the repo root (`./llama.cpp/...`, `models/...`,
  `tests/ai_workloads/...`). `cd` into the repo before running.
* **Each collector reruns the benchmark.** mantis-monitor runs the workload
  once per collector, and perf re-runs it once per counter group. So a single
  config executes the AI workload several times. That is intentional (it is how
  the model-load disk reads feed the BPF io_latency collector), but keep models
  small and `iterations: 1` while validating.
* **Make a `models/` directory** at the repo root to hold downloaded weights:
  ```bash
  mkdir -p models
  ```

---

## 1. llama.cpp  (LLM inference)

Representative transformer inference (prompt prefill + token generation) via
the purpose-built `llama-bench` tool. Loading the GGUF weights from disk gives
the BPF io_latency collector real read traffic; generation pins the CPU/GPU.

### 1a. Get the source

```bash
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
```

### 1b. Build — pick ONE backend

**CPU only:**
```bash
cmake -B build
cmake --build build --config Release -j
```

**NVIDIA (CUDA)** — needs the CUDA toolkit:
```bash
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j
```

**AMD (HIP/ROCm)** — needs ROCm + HIP:
```bash
cmake -B build -DGGML_HIP=ON -DAMDGPU_TARGETS=$(rocminfo | grep -m1 -o 'gfx[0-9a-f]*')
cmake --build build --config Release -j
```

The benchmark binary lands at `llama.cpp/build/bin/llama-bench`. Verify:
```bash
./build/bin/llama-bench --help
cd ..   # back to repo root
```

### 1c. Download a small GGUF model

Any GGUF works; a small quantized model keeps load/compute modest. Examples
(pick one, save into `models/`):

```bash
# Qwen2.5-0.5B (tiny, fast) — needs huggingface-cli (pip install -U "huggingface_hub[cli]")
huggingface-cli download Qwen/Qwen2.5-0.5B-Instruct-GGUF qwen2.5-0.5b-instruct-q4_k_m.gguf \
    --local-dir models
# …or TinyLlama-1.1B:
# huggingface-cli download TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf --local-dir models
```

Make sure the filename in the test config's `cmd:` matches what you downloaded
(the configs default to `models/qwen2.5-0.5b-instruct-q4_k_m.gguf`).

### 1d. Run

```bash
# from the repo root, with the venv active
mantis-monitor tests/test_ai_llamacpp_cpu.yaml      # or _nvidia / _amd
```

The GPU configs add `-ngl 99` to offload all layers to the GPU — that only
works if you built with the CUDA/HIP backend above.

---

## 2. ONNX Runtime  (CV / NLP inference)

Representative inference over standard ONNX models (default: ResNet-50). Driven
by the bundled helper `tests/ai_workloads/onnx_infer_bench.py`, which loads the
model, fabricates correctly-typed random inputs, and runs a timed inference
loop on the chosen execution provider.

### 2a. Install onnxruntime — pick ONE matching your hardware

```bash
# CPU
pip install onnxruntime numpy

# NVIDIA (CUDA execution provider)
pip install onnxruntime-gpu numpy

# AMD (ROCm execution provider) — availability depends on your ROCm version;
# you may need AMD's wheel index or to build ORT from source with --use_rocm.
pip install onnxruntime-rocm numpy   # if a matching wheel exists for your ROCm
```

Sanity-check the provider is present:
```bash
python3 -c "import onnxruntime as o; print(o.get_available_providers())"
# CPU build  -> ['CPUExecutionProvider']
# GPU builds -> include 'CUDAExecutionProvider' or 'ROCMExecutionProvider'
```

### 2b. Download a model

```bash
# ResNet-50 v1 (ONNX model zoo)
curl -L -o models/resnet50-v1-7.onnx \
  https://github.com/onnx/models/raw/main/validated/vision/classification/resnet/model/resnet50-v1-7.onnx
```

Any ONNX model works — point `--model` at it. The helper auto-detects input
shapes/types and substitutes `1` for dynamic dimensions (override with
`--dynamic-dim`).

### 2c. Run

```bash
mantis-monitor tests/test_ai_onnx_cpu.yaml      # or _nvidia / _amd
```

The helper accepts `--provider {cpu,cuda,rocm,migraphx,tensorrt}`, `--runs`,
`--warmup`, `--intra-threads`. The AMD config uses `--provider rocm`; if you
run through MIGraphX instead, change it to `migraphx`.

You can test the driver directly without mantis-monitor:
```bash
python3 tests/ai_workloads/onnx_infer_bench.py --model models/resnet50-v1-7.onnx --provider cpu --runs 50
```

---

## 3. MLPerf Inference  (MLCommons)

The industry-standard, most "representative" (and heaviest) option. Run via the
MLCommons CM automation, which fetches the model + dataset and builds the
LoadGen harness.

### 3a. Install the MLCommons CM automation

```bash
pip install cmind
cm pull repo mlcommons@mlperf-automations
```

(The newer MLCFlow front-end — `pip install mlc-scripts`, driver `mlcr` — runs
the same scripts; adapt the `cm run script` commands below to `mlcr` if you
prefer it.)

### 3b. Backend for your hardware

* **CPU:** `pip install onnxruntime` (the configs use `--framework=onnxruntime
  --device=cpu`).
* **NVIDIA:** `pip install onnxruntime-gpu`; the config uses `--device=cuda`.
  For the optimized NVIDIA harness instead of the reference implementation,
  switch `--implementation=reference` to `--implementation=nvidia` (much
  heavier; needs TensorRT/Docker per MLCommons docs).
* **AMD:** runs through the onnxruntime ROCm EP where supported. AMD coverage in
  the MLPerf *reference* implementation is limited and version-dependent — if
  `--device=rocm` is rejected, use `test_ai_onnx_amd.yaml` for a reliable AMD
  AI workload instead.

### 3c. WARM THE CACHE FIRST (important)

Run the benchmark once standalone so CM downloads the model/dataset and builds
the harness **before** you measure. Otherwise the first mantis-monitor run
downloads multi-GB artifacts mid-measurement and re-downloads them for every
collector.

```bash
# CPU example — do the analogous run with --device=cuda / --device=rocm
cm run script --tags=run-mlperf,inference,_performance-only \
  --model=resnet50 --implementation=reference --framework=onnxruntime \
  --category=edge --scenario=Offline --device=cpu --quiet
```

After this completes once, the artifacts are cached and subsequent runs reuse
them.

### 3d. Run under mantis-monitor

```bash
mantis-monitor tests/test_ai_mlperf_cpu.yaml      # or _nvidia / _amd
```

The configs pass `--rerun` so CM re-executes the (already-built) benchmark each
time rather than short-circuiting on a cached result.

---

## Quick reference — what each config needs

| Config | Engine setup | Collector setup |
|--------|--------------|-----------------|
| `test_ai_llamacpp_cpu`    | §1 CPU build + GGUF model | SETUP.md |
| `test_ai_llamacpp_nvidia` | §1 CUDA build + GGUF model | SETUP.md + SETUP_GPU.md (nvidia) |
| `test_ai_llamacpp_amd`    | §1 HIP build + GGUF model | SETUP.md + SETUP_GPU.md (rocm) |
| `test_ai_onnx_cpu`        | §2 `onnxruntime` + model | SETUP.md |
| `test_ai_onnx_nvidia`     | §2 `onnxruntime-gpu` + model | SETUP.md + SETUP_GPU.md (nvidia) |
| `test_ai_onnx_amd`        | §2 `onnxruntime-rocm` + model | SETUP.md + SETUP_GPU.md (rocm) |
| `test_ai_mlperf_cpu`      | §3 CM + warm cache (cpu) | SETUP.md |
| `test_ai_mlperf_nvidia`   | §3 CM + warm cache (cuda) | SETUP.md + SETUP_GPU.md (nvidia) |
| `test_ai_mlperf_amd`      | §3 CM + warm cache (rocm) | SETUP.md + SETUP_GPU.md (rocm) |
