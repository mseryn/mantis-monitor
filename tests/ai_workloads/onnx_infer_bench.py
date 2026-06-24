#!/usr/bin/env python3
# This file is part of the Mantis-Monitor data collection suite.
#
# A small, dependency-light ONNX Runtime inference benchmark used by the
# mantis-monitor AI example configs (tests/test_ai_onnx_*.yaml).
#
# The pip `onnxruntime` wheels do not ship the `onnxruntime_perf_test` C++
# tool, so this script provides an equivalent, portable driver: it loads an
# ONNX model, fabricates correctly-typed random inputs, and runs inference in
# a timed loop on the requested execution provider (CPU / CUDA / ROCm).
#
# It deliberately does NOT check output correctness — it exists to generate a
# representative, sustained inference compute load for the perf / BPF / pfs /
# GPU collectors to measure.
#
# Examples:
#   python3 onnx_infer_bench.py --model resnet50.onnx --provider cpu  --runs 200
#   python3 onnx_infer_bench.py --model resnet50.onnx --provider cuda --runs 500
#   python3 onnx_infer_bench.py --model bert.onnx     --provider rocm --runs 300

import argparse
import sys
import time

import numpy as np

try:
    import onnxruntime as ort
except ImportError:  # pragma: no cover
    sys.exit(
        "onnxruntime is not installed.\n"
        "  CPU:    pip install onnxruntime\n"
        "  NVIDIA: pip install onnxruntime-gpu\n"
        "  AMD:    pip install onnxruntime-rocm  (or build ORT with the ROCm EP)\n"
        "See SETUP_AI.md for details."
    )


# Map ONNX Runtime tensor type strings to numpy dtypes.
_TYPE_MAP = {
    "tensor(float)":   np.float32,
    "tensor(float16)": np.float16,
    "tensor(double)":  np.float64,
    "tensor(int64)":   np.int64,
    "tensor(int32)":   np.int32,
    "tensor(int16)":   np.int16,
    "tensor(int8)":    np.int8,
    "tensor(uint8)":   np.uint8,
    "tensor(bool)":    np.bool_,
}

# Friendly provider aliases -> ONNX Runtime execution provider names.
_PROVIDER_MAP = {
    "cpu":  "CPUExecutionProvider",
    "cuda": "CUDAExecutionProvider",
    "rocm": "ROCMExecutionProvider",
    "migraphx": "MIGraphXExecutionProvider",
    "tensorrt": "TensorrtExecutionProvider",
}


def build_inputs(session, dynamic_dim):
    """
    Fabricate one random input feed dict matching the model's input specs.

    Dynamic / symbolic dimensions (None or strings such as "batch_size") are
    replaced by ``dynamic_dim``. Integer tensors are filled with small indices
    (0/1) so they stay within any embedding vocabulary; floats use a normal
    distribution; bools are random.

    :param session: an ``onnxruntime.InferenceSession``
    :param dynamic_dim: int to substitute for unknown dimensions
    :returns: dict mapping input name -> numpy array
    """
    feeds = {}
    for inp in session.get_inputs():
        shape = []
        for dim in inp.shape:
            shape.append(dim if isinstance(dim, int) and dim > 0 else dynamic_dim)
        dtype = _TYPE_MAP.get(inp.type, np.float32)
        if np.issubdtype(dtype, np.floating):
            feeds[inp.name] = np.random.randn(*shape).astype(dtype)
        elif dtype == np.bool_:
            feeds[inp.name] = np.random.randint(0, 2, size=shape).astype(np.bool_)
        else:  # integer types — keep indices tiny so they're always in-vocab
            feeds[inp.name] = np.random.randint(0, 2, size=shape).astype(dtype)
    return feeds


def main():
    parser = argparse.ArgumentParser(description="Minimal ONNX Runtime inference benchmark")
    parser.add_argument("--model", required=True, help="Path to the .onnx model file")
    parser.add_argument("--provider", default="cpu",
                        choices=sorted(_PROVIDER_MAP.keys()),
                        help="Execution provider (default: cpu)")
    parser.add_argument("--runs", type=int, default=200, help="Timed inference iterations")
    parser.add_argument("--warmup", type=int, default=10, help="Warmup iterations (untimed)")
    parser.add_argument("--dynamic-dim", type=int, default=1,
                        help="Value to substitute for dynamic input dimensions (default: 1)")
    parser.add_argument("--intra-threads", type=int, default=0,
                        help="intra_op_num_threads (0 = ORT default)")
    args = parser.parse_args()

    provider = _PROVIDER_MAP[args.provider]
    available = ort.get_available_providers()
    if provider not in available:
        sys.exit(
            "Execution provider '{}' ({}) is not available in this onnxruntime build.\n"
            "Available providers: {}\n"
            "Install the matching package (see SETUP_AI.md).".format(
                args.provider, provider, ", ".join(available)
            )
        )

    sess_options = ort.SessionOptions()
    if args.intra_threads > 0:
        sess_options.intra_op_num_threads = args.intra_threads

    print("Loading model: {}".format(args.model))
    session = ort.InferenceSession(args.model, sess_options, providers=[provider])
    feeds = build_inputs(session, args.dynamic_dim)

    print("Provider: {} | warmup: {} | timed runs: {}".format(provider, args.warmup, args.runs))
    for _ in range(args.warmup):
        session.run(None, feeds)

    start = time.time()
    for _ in range(args.runs):
        session.run(None, feeds)
    elapsed = time.time() - start

    per_infer_ms = (elapsed / args.runs) * 1000.0 if args.runs else float("nan")
    throughput = args.runs / elapsed if elapsed > 0 else float("nan")
    print("Total: {:.3f} s | {:.3f} ms/infer | {:.1f} infer/s".format(
        elapsed, per_infer_ms, throughput))


if __name__ == "__main__":
    main()
