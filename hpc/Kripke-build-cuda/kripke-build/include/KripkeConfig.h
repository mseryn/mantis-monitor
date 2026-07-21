#ifndef KRIPKE_CONFIG_H__
#define KRIPKE_CONFIG_H__

#define KRIPKE_VERSION "1.2.5-dev"

#define KRIPKE_CXX_COMPILER "/usr/bin/g++-13"
#define KRIPKE_CXX_FLAGS "       "
#define KRIPKE_LINK_FLAGS " "

/* #undef KRIPKE_USE_MPI */
/* #undef KRIPKE_USE_OPENMP */
#define KRIPKE_USE_CUDA
/* #undef KRIPKE_USE_CHAI */
/* #undef KRIPKE_USE_CHAI_SINGLE_MEMORY */
/* #undef KRIPKE_USE_HIP */

/* #undef KRIPKE_USE_CALIPER */

#define KRIPKE_ARCH "CUDA"

#define KRIPKE_ARCHV_DEFAULT ArchV_CUDA
#define KRIPKE_LAYOUTV_DEFAULT LayoutV_DGZ

#define KRIPKE_NVCC_COMPILER "/usr/bin/nvcc"
#define KRIPKE_NVCC_FLAGS "-ccbin=/usr/bin/g++-13 --extended-lambda -arch=sm_75 -O3 -DNDEBUG"

#endif
