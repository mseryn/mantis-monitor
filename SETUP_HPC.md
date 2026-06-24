# Mantis-Monitor HPC Benchmark Setup Guide

Build/run instructions for the HPC proxy-app / mini-app benchmark suite wired
up as mantis-monitor example configs. Each benchmark has up to three variants —
**CPU**, **NVIDIA**, **AMD** — depending on which programming-model backends
the upstream code supports (AMD is provided only where a first-class HIP or
portability-framework backend exists).

All configs collect with **perf + BPF (io_latency) + pfs (utilization)**; the
NVIDIA variants add the **nvidia** collector and the AMD variants add the
**rocm** collector.

> This guide is organized in **batches by scientific domain** (1–7), matching
> the benchmark matrix. All sections are present below.
>
> Build commands are sensible starting points; exact CMake flags, Makefile
> targets, binary names, GPU-arch flags (`-DCMAKE_CUDA_ARCHITECTURES`,
> `-DCMAKE_HIP_ARCHITECTURES`, `--offload-arch`), and input-deck paths vary by
> upstream version — check each repo's README and adjust the config `cmd:`
> accordingly. Problem sizes are deliberately small; scale them up for longer
> runs.

## Conventions used by every config

* **Clone/build each benchmark under `./hpc/<Name>/`** at the repo root. The
  configs reference binaries by that relative path (e.g.
  `./hpc/XSBench/cuda/XSBench`). Create the directory once:
  ```bash
  mkdir -p hpc
  ```
* **Run mantis-monitor from the repo root** (the working directory it is
  launched from is where the benchmark's relative paths resolve).
* **Each collector reruns the benchmark** (perf re-runs once per counter
  group), so a single config executes the workload several times. Keep problem
  sizes small while validating; every config defaults to `iterations: 1`.
* **Collector permissions** must be set up first:
  * perf + BPF + pfs → [`SETUP.md`](SETUP.md)
  * `nvidia-smi` (NVIDIA variants) → [`SETUP_GPU.md`](SETUP_GPU.md)
  * `rocm-smi` (AMD variants) → [`SETUP_GPU.md`](SETUP_GPU.md)
* **Problem sizes** in the example commands are deliberately small (target a
  few seconds–minutes per run, well under an hour). Each section notes the
  knobs to scale up.

## Toolchains you will need

* **CPU variants:** a C/C++/Fortran compiler with OpenMP (gcc/clang/gfortran).
* **NVIDIA variants:** CUDA Toolkit (`nvcc`); a few benchmarks want the NVHPC
  compilers for OpenACC.
* **AMD variants:** ROCm + HIP (`hipcc`). Portability-framework benchmarks
  (RAJA/Kokkos) are configured with their HIP backend.
* **CMake** ≥ 3.18 and **git** for most builds.

---

# Batch 1 — Particle transport (nuclear)

Configs: `test_hpc_{xsbench,rsbench,quicksilver,kripke,snap}_{cpu,nvidia,amd}.yaml`
(SNAP is CPU + NVIDIA only — no first-class HIP backend.)

## XSBench / RSBench

Monte Carlo neutron cross-section lookup proxies (ANL). Both build one binary
per backend directory, and both already have *native* Mantis Benchmark classes
— but these example configs intentionally use `generic_benchmark` wrappers so
the whole HPC suite is consistent and needs no code changes.

```bash
cd hpc
git clone https://github.com/ANL-CESAR/XSBench.git
git clone https://github.com/ANL-CESAR/RSBench.git
cd ..
```

Each repo has one subdirectory per programming model; `cd` into the one you
want and `make`:

```bash
# XSBench — CPU (OpenMP threading)
make -C hpc/XSBench/openmp-threading
# XSBench — NVIDIA (CUDA): edit the Makefile's CUDA arch (SM) if needed
make -C hpc/XSBench/cuda
# XSBench — AMD (HIP)
make -C hpc/XSBench/hip

# RSBench — same layout
make -C hpc/RSBench/openmp-threading
make -C hpc/RSBench/cuda
make -C hpc/RSBench/hip
```

Run knobs (set in the config `cmd:`): `-m event` (event-based mode),
`-s {small,large,XL}` (problem size), `-l <N>` (number of lookups). Start with
`-s small`; bump to `large` for a longer run.

```bash
# example: validate a binary by hand before profiling
./hpc/XSBench/openmp-threading/XSBench -m event -s small
```

Then:
```bash
mantis-monitor tests/test_hpc_xsbench_cpu.yaml      # or _nvidia / _amd
mantis-monitor tests/test_hpc_rsbench_cpu.yaml      # or _nvidia / _amd
```

## Quicksilver

Monte Carlo dynamic particle transport proxy (LLNL). The backend is selected at
**build** time, so build once per backend into a separate directory:

```bash
cd hpc
git clone https://github.com/LLNL/Quicksilver.git
cd Quicksilver/src

# CPU (OpenMP)
make -j && mkdir -p ../build-openmp && cp qs ../build-openmp/
# NVIDIA (CUDA): rebuild with the CUDA flags enabled in the Makefile
make clean && make -j CUDA=1 && mkdir -p ../build-cuda && cp qs ../build-cuda/
# AMD (HIP): rebuild with the HIP flags enabled
make clean && make -j HIP=1 && mkdir -p ../build-hip && cp qs ../build-hip/
cd ../../..
```

> Quicksilver's Makefile toggles backends via compile flags — see its
> `src/Makefile` for the exact `CUDA`/`HIP` variables for your version. The
> copy-into-`build-*` step above matches the paths in the configs.

Problem size comes from the input deck (`-i`) and `-n <particles>`. The configs
point at a small scattering example and cap particles at 100k:

```bash
./hpc/Quicksilver/build-openmp/qs \
  -i ./hpc/Quicksilver/Examples/AllScattering/scatteringOnly.inp -n 100000
```

Pick any deck under `hpc/Quicksilver/Examples/`; reduce `-n` for shorter runs.

```bash
mantis-monitor tests/test_hpc_quicksilver_cpu.yaml   # or _nvidia / _amd
```

## Kripke

Structured deterministic Sₙ transport mini-app (LLNL), built on RAJA. Backends
are compiled in via CMake and selected at runtime with `--arch`:

```bash
cd hpc
git clone --recursive https://github.com/LLNL/Kripke.git
cd Kripke

# CPU (OpenMP)
cmake -B ../Kripke-build-openmp -DENABLE_OPENMP=On
cmake --build ../Kripke-build-openmp -j
mkdir -p build-openmp && cp ../Kripke-build-openmp/kripke.exe build-openmp/

# NVIDIA (CUDA)
cmake -B ../Kripke-build-cuda -DENABLE_CUDA=On
cmake --build ../Kripke-build-cuda -j
mkdir -p build-cuda && cp ../Kripke-build-cuda/kripke.exe build-cuda/

# AMD (HIP)
cmake -B ../Kripke-build-hip -DENABLE_HIP=On
cmake --build ../Kripke-build-hip -j
mkdir -p build-hip && cp ../Kripke-build-hip/kripke.exe build-hip/
cd ../..
```

Problem size: `--zones X,Y,Z` and `--niter N` (plus `--groups`, `--quad`,
`--legendre`). The configs use `--zones 32,32,32 --niter 10`.

```bash
mantis-monitor tests/test_hpc_kripke_cpu.yaml        # or _nvidia / _amd
```

## SNAP  (CPU + NVIDIA only)

SN (discrete ordinates) Application Proxy for PARTISN (LANL), Fortran + OpenMP,
with a GPU path via OpenACC. No first-class HIP backend, so there is no AMD
variant.

```bash
cd hpc
git clone https://github.com/lanl/SNAP.git
cd SNAP

# CPU (OpenMP) — produces src/snap
make -C src

# NVIDIA (OpenACC) — build with an NVHPC (PGI) compiler into a separate dir.
# Adjust SNAP's Makefile compiler/flags for OpenACC, then:
#   make -C src   # output copied to src-acc/snap
mkdir -p src-acc   # place the OpenACC-built `snap` binary here
cd ../..
```

SNAP reads an input deck and writes an output file; problem size is set in the
deck. Provide a small deck at `hpc/SNAP/inputs/small.inp` (start from one of the
decks in the repo's `qasnap`/`doc` examples and shrink the spatial/angular
dimensions).

```bash
./hpc/SNAP/src/snap ./hpc/SNAP/inputs/small.inp snap_cpu_out.txt
mantis-monitor tests/test_hpc_snap_cpu.yaml          # or _nvidia
```

> SNAP build details vary by compiler (gfortran vs NVHPC) and version — consult
> the repo's `README`/`Makefile`. The configs assume the CPU binary at
> `src/snap` and the GPU binary at `src-acc/snap`.

---

# Batch 2 — Hydrodynamics & CFD

Configs: `test_hpc_{cloverleaf,laghos}_{cpu,nvidia,amd}.yaml`,
`test_hpc_{lulesh,pennant,nekbone}_{cpu,nvidia}.yaml` (LULESH/PENNANT/Nekbone
have no clean upstream HIP backend → CPU + NVIDIA only).

## CloverLeaf / TeaLeaf

Both are UoB-HPC single-source ports built with CMake `-DMODEL=<backend>`. One
build directory per backend (binary `clover_leaf` / `tealeaf`):

```bash
cd hpc
git clone https://github.com/UoB-HPC/CloverLeaf.git
git clone https://github.com/UoB-HPC/TeaLeaf.git
cd ..

# CloverLeaf — repeat the same three for TeaLeaf
cmake -S hpc/CloverLeaf -B hpc/CloverLeaf/build-omp  -DMODEL=omp
cmake --build hpc/CloverLeaf/build-omp -j
cmake -S hpc/CloverLeaf -B hpc/CloverLeaf/build-cuda -DMODEL=cuda -DCMAKE_CUDA_ARCHITECTURES=80
cmake --build hpc/CloverLeaf/build-cuda -j
cmake -S hpc/CloverLeaf -B hpc/CloverLeaf/build-hip  -DMODEL=hip  -DCMAKE_HIP_ARCHITECTURES=gfx90a
cmake --build hpc/CloverLeaf/build-hip -j
```

Input decks live in `InputDecks/`; the configs use the short benchmark decks
(`clover_bm_short.in` / `tea_bm_short.in`). Check the repo README for the exact
`-DMODEL` names available in your version (omp/cuda/hip/kokkos/sycl/…).

## LULESH  (CPU + NVIDIA)

```bash
cd hpc && git clone https://github.com/LLNL/LULESH.git && cd ..
# CPU (OpenMP):
cmake -S hpc/LULESH -B hpc/LULESH/build-omp -DWITH_MPI=OFF -DWITH_OPENMP=ON
cmake --build hpc/LULESH/build-omp -j        # -> lulesh2.0
# NVIDIA: build the CUDA sources (cuda branch / cuda/ dir) into build-cuda -> lulesh
```

Run knobs: `-s <mesh edge>`, `-i <iters>`.

## PENNANT  (CPU + NVIDIA)

```bash
cd hpc && git clone https://github.com/lanl/PENNANT.git && cd ..
# CPU: edit Makefile for OpenMP, `make`, copy build/pennant -> build-omp/pennant
# NVIDIA: use the CUDA Makefile variant -> build-cuda/pennant
```

Decks under `test/`; `leblanc/leblanc.pnt` is small, `leblancbig/` is longer.

## Laghos  (CPU / NVIDIA / AMD)

Depends on hypre + METIS + MFEM. Build MFEM with CUDA/HIP for the GPU variants,
then build Laghos against it; select the device at runtime with `-d cpu|cuda|hip`:

```bash
# 1) build MFEM (serial, or with CUDA/HIP) per https://mfem.org
cd hpc && git clone https://github.com/CEED/Laghos.git && cd Laghos
make            # links your MFEM; place binaries at build-cpu/ build-cuda/ build-hip/
cd ../..
```

Run knobs: `-p <problem>`, `-rs <refines>`, `-tf <final time>`.

## Nekbone  (CPU + NVIDIA)

```bash
cd hpc && git clone https://github.com/Nek5000/Nekbone.git && cd ..
# CPU: cd Nekbone/test/example1 && ./makenek ... -> nekbone
# NVIDIA: use a CUDA Nekbone fork (Nekbone CUDA / NekBench) -> Nekbone-cuda/test/nekbone
```

Problem size is set in the example's `SIZE` / `data.rea` files.

---

# Batch 3 — Solvers / multigrid / FEM

Configs: `test_hpc_{tealeaf,hpcg,amg2023,minife}_{cpu,nvidia,amd}.yaml`,
`test_hpc_hpgmg_{cpu,nvidia}.yaml`. (TeaLeaf build is in the CloverLeaf/TeaLeaf
section above.)

## HPCG  (CPU / NVIDIA / AMD)

```bash
# CPU reference
cd hpc && git clone https://github.com/hpcg-benchmark/hpcg.git
cd hpcg && mkdir build && cd build && ../configure Linux_Serial && make   # -> bin/xhpcg
cd ../../..
# NVIDIA: use NVIDIA's prebuilt HPCG (NVIDIA HPC-Benchmarks container/package) -> hpc/hpcg-nvidia/xhpcg
# AMD: rocHPCG
git clone https://github.com/ROCm/rocHPCG.git hpc/rocHPCG
cd hpc/rocHPCG && ./install.sh   # -> build/bin/rochpcg
cd ../..
```

Run knobs: `--nx/--ny/--nz` (local grid) and `--rt <seconds>` (kept short here;
official runs use ≥1800 s).

## AMG2023  (CPU / NVIDIA / AMD)

Build HYPRE (add `--with-cuda` / `--with-hip` for GPU), then AMG2023 against it:

```bash
cd hpc && git clone https://github.com/LLNL/AMG2023.git
# configure with your HYPRE; build into build-cpu / build-cuda / build-hip -> test/amg
```

Run knobs: `-n <nx ny nz>` (per-rank grid), `-P <px py pz>` (process grid).

## miniFE  (CPU / NVIDIA / AMD)

```bash
cd hpc && git clone https://github.com/Mantevo/miniFE.git
# CPU: build miniFE/openmp -> openmp/src/miniFE.x
# NVIDIA: build the Kokkos variant with Kokkos+CUDA -> kokkos/src/miniFE.x
# AMD:    build the Kokkos variant with Kokkos+HIP  -> kokkos-hip/src/miniFE.x
```

Run knobs: `nx= ny= nz=`.

## HPGMG  (CPU + NVIDIA)

```bash
cd hpc && git clone https://bitbucket.org/hpgmg/hpgmg.git   # or a github mirror
# CPU finite-volume: ./build.sh -> build/bin/hpgmg-fv
# NVIDIA: NVIDIA's hpgmg-cuda (or the CUDA branch) -> hpgmg-cuda/build/bin/hpgmg-fv
```

Args: `<log2 box size> <boxes per rank>` (configs use `6 8`).

---

# Batch 4 — Molecular dynamics / chemistry / QMC

Configs: `test_hpc_{minibude,gromacs}_{cpu,nvidia,amd}.yaml`,
`test_hpc_{comd,miniqmc}_{cpu,nvidia}.yaml`.

## CoMD  (CPU + NVIDIA)

```bash
cd hpc && git clone https://github.com/ECP-copa/CoMD.git
# CPU: cd CoMD/src-openmp && make -> ../bin/CoMD-openmp
# NVIDIA: use a CUDA CoMD fork -> CoMD-cuda/bin/CoMD-cuda
```

Run knobs: `-x -y -z` (unit cells), `-e` (EAM potential).

## miniBUDE  (CPU / NVIDIA / AMD)

UoB-HPC CMake `-DMODEL=<backend>`, same pattern as CloverLeaf (binary `bude`):

```bash
cd hpc && git clone https://github.com/UoB-HPC/miniBUDE.git && cd ..
cmake -S hpc/miniBUDE -B hpc/miniBUDE/build-omp  -DMODEL=omp  && cmake --build hpc/miniBUDE/build-omp -j
cmake -S hpc/miniBUDE -B hpc/miniBUDE/build-cuda -DMODEL=cuda && cmake --build hpc/miniBUDE/build-cuda -j
cmake -S hpc/miniBUDE -B hpc/miniBUDE/build-hip  -DMODEL=hip  && cmake --build hpc/miniBUDE/build-hip -j
```

Run knobs: `--deck data/bm1` (or `bm2`), `-i <iters>`.

## miniQMC  (CPU + NVIDIA)

```bash
cd hpc && git clone https://github.com/QMCPACK/miniqmc.git && cd ..
cmake -S hpc/miniqmc -B hpc/miniqmc/build && cmake --build hpc/miniqmc/build -j      # CPU -> build/bin/miniqmc
# NVIDIA: configure with -DENABLE_OFFLOAD=ON (OpenMP target) -> build-offload/bin/miniqmc
```

Run knobs: `-g "nx ny nz"` (supercell tiling).

## GROMACS  (CPU / NVIDIA / AMD)

```bash
cd hpc && git clone https://gitlab.com/gromacs/gromacs.git
# CPU:    cmake -DGMX_GPU=OFF                              -> build-cpu/bin/gmx
# NVIDIA: cmake -DGMX_GPU=CUDA                             -> build-cuda/bin/gmx
# AMD:    cmake -DGMX_GPU=SYCL -DGMX_SYCL=ACPP (hipSYCL)   -> build-hip/bin/gmx
```

Drop a benchmark `.tpr` (e.g. the Max-Planck benchMEM/benchPEP sets) into
`hpc/gromacs/bench/`. Run knobs: `-nsteps`, `-resethway`, `-noconfout`,
`-nb cpu|gpu`.

---

# Batch 5 — Memory / kernels / FFT

Configs: `test_hpc_{babelstream,rajaperf,heffte}_{cpu,nvidia,amd}.yaml`.

## BabelStream  (CPU / NVIDIA / AMD)

```bash
cd hpc && git clone https://github.com/UoB-HPC/BabelStream.git && cd ..
cmake -S hpc/BabelStream -B hpc/BabelStream/build-omp  -DMODEL=omp  && cmake --build hpc/BabelStream/build-omp -j   # omp-stream
cmake -S hpc/BabelStream -B hpc/BabelStream/build-cuda -DMODEL=cuda && cmake --build hpc/BabelStream/build-cuda -j  # cuda-stream
cmake -S hpc/BabelStream -B hpc/BabelStream/build-hip  -DMODEL=hip  && cmake --build hpc/BabelStream/build-hip -j   # hip-stream
```

Run knobs: `-s <elements>`, `-n <reps>`.

## RAJAPerf  (CPU / NVIDIA / AMD)

```bash
cd hpc && git clone --recursive https://github.com/LLNL/RAJAPerf.git && cd ..
cmake -S hpc/RAJAPerf -B hpc/RAJAPerf/build-omp  -DENABLE_OPENMP=On && cmake --build hpc/RAJAPerf/build-omp -j
cmake -S hpc/RAJAPerf -B hpc/RAJAPerf/build-cuda -DENABLE_CUDA=On   && cmake --build hpc/RAJAPerf/build-cuda -j
cmake -S hpc/RAJAPerf -B hpc/RAJAPerf/build-hip  -DENABLE_HIP=On    && cmake --build hpc/RAJAPerf/build-hip -j
```

Binary `bin/raja-perf.exe`. Knobs: `-v Base_OpenMP|Base_CUDA|Base_HIP`,
`--npasses 1`, or `-k <kernel>` to restrict to specific kernels.

## heFFTe  (CPU / NVIDIA / AMD)

```bash
cd hpc && git clone https://github.com/icl-utk-edu/heffte.git && cd ..
cmake -S hpc/heffte -B hpc/heffte/build \
  -DHeffte_ENABLE_FFTW=ON -DHeffte_ENABLE_CUDA=ON -DHeffte_ENABLE_ROCM=ON
cmake --build hpc/heffte/build -j        # -> build/benchmarks/speed3d_c2c
```

Needs an MPI launcher even for 1 rank:
`mpirun -np 1 speed3d_c2c <fftw|cufft|rocfft> double <nx ny nz>`.

---

# Batch 6 — Physics, geoscience, climate

Configs: `test_hpc_{su3_bench,sw4lite,warpx,miniweather}_{cpu,nvidia,amd}.yaml`,
`test_hpc_haccmk_{cpu,nvidia}.yaml`.

## su3_bench  (CPU / NVIDIA / AMD)

```bash
cd hpc && git clone https://github.com/NERSC/su3_bench.git && cd su3_bench
make -f Makefile.openmp     # -> su3_bench_openmp (rename per the repo's targets)
make -f Makefile.cuda       # -> su3_bench_cuda
make -f Makefile.hip        # -> su3_bench_hip
cd ../..
```

The configs expect binaries named `su3_bench_{openmp,cuda,hip}`; adjust to your
Makefile's actual output names. No runtime args (fixed problem).

## HACCmk  (CPU + NVIDIA)

Part of the CORAL-2 benchmark suite (asc.llnl.gov/coral-2-benchmarks). Build the
OpenMP microkernel `hacc_omp.exe`; the CUDA variant `hacc_cuda.exe` comes from
the GPU port. Both run a fixed compute kernel (no args).

## SW4lite  (CPU / NVIDIA / AMD)

```bash
cd hpc && git clone https://github.com/geodynamics/sw4lite.git && cd sw4lite
make                # CPU -> optimize/sw4lite
# GPU: build the RAJA/CUDA and RAJA/HIP variants -> optimize_cuda/sw4lite, optimize_hip/sw4lite
cd ../..
```

Run with an input deck, e.g. `tests/pointsource/pointsource.in`.

## WarpX  (CPU / NVIDIA / AMD)

```bash
cd hpc && git clone https://github.com/ECP-WarpX/WarpX.git && cd ..
cmake -S hpc/WarpX -B hpc/WarpX/build-omp  -DWarpX_COMPUTE=OMP  -DWarpX_DIMS=3 && cmake --build hpc/WarpX/build-omp -j
cmake -S hpc/WarpX -B hpc/WarpX/build-cuda -DWarpX_COMPUTE=CUDA -DWarpX_DIMS=3 && cmake --build hpc/WarpX/build-cuda -j
cmake -S hpc/WarpX -B hpc/WarpX/build-hip  -DWarpX_COMPUTE=HIP  -DWarpX_DIMS=3 && cmake --build hpc/WarpX/build-hip -j
```

Binary `bin/warpx.3d`. Pass an example input + `max_step=<N>` to cap timesteps.

## miniWeather  (CPU / NVIDIA / AMD)

```bash
cd hpc && git clone https://github.com/mrnorman/miniWeather.git
# CMake build; pick the source variant per backend:
#   openmp (CPU) / openacc (NVIDIA) / kokkos with Kokkos+HIP (AMD)
```

Problem size (NX/NZ/SIM_TIME) is set via CMake `-D` defines / source constants —
see the repo README. Reduce SIM_TIME for short runs.

---

# Batch 7 — Graph analytics + CFD kernel suite

Configs: `test_hpc_gapbs_cpu.yaml`, `test_hpc_gunrock_nvidia.yaml`,
`test_hpc_npb_{cpu,nvidia}.yaml`.

## gapbs  (CPU only)

```bash
cd hpc && git clone https://github.com/sbeamer/gapbs.git && cd gapbs && make   # -> bfs, pr, sssp, bc, cc, tc
cd ../..
```

Run knobs: `-g <scale>` (2^scale-vertex Kronecker graph), `-n <trials>`. Swap
`bfs` for `pr`/`sssp`/`cc`/etc.

## Gunrock  (NVIDIA only)

```bash
cd hpc && git clone --recursive https://github.com/gunrock/gunrock.git
cmake -S gunrock -B gunrock/build && cmake --build gunrock/build -j      # -> build/bin/bfs
```

Provide a Matrix-Market graph (the repo ships small datasets under
`datasets/`). The CLI differs between classic Gunrock and "essentials" — adjust
the config `cmd:` to match your build.

## NPB  (CPU + NVIDIA)

```bash
# CPU (NPB-OMP): from the NASA NPB3.x distribution
#   cd hpc/NPB-OMP/NPB3.x-OMP && make CG CLASS=B   -> bin/cg.B.x
# NVIDIA (NPB-GPU CUDA port):
cd hpc && git clone https://github.com/GMAP/NPB-GPU.git
#   build the CUDA CG, class B -> NPB-GPU/bin/cg.B
```

Swap `cg` for `ep/ft/mg/lu/sp/bt`; class `A` is shorter, `C` longer.
