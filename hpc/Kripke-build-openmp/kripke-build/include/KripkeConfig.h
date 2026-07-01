#ifndef KRIPKE_CONFIG_H__
#define KRIPKE_CONFIG_H__

#define KRIPKE_VERSION "1.2.5-dev"

#define KRIPKE_CXX_COMPILER "/usr/bin/c++"
#define KRIPKE_CXX_FLAGS "       "
#define KRIPKE_LINK_FLAGS " "

/* #undef KRIPKE_USE_MPI */
#define KRIPKE_USE_OPENMP
/* #undef KRIPKE_USE_CUDA */
/* #undef KRIPKE_USE_CHAI */
/* #undef KRIPKE_USE_CHAI_SINGLE_MEMORY */
/* #undef KRIPKE_USE_HIP */

/* #undef KRIPKE_USE_CALIPER */

#define KRIPKE_ARCH "OpenMP"

#define KRIPKE_ARCHV_DEFAULT ArchV_OpenMP
#define KRIPKE_LAYOUTV_DEFAULT LayoutV_DGZ

/* #undef KRIPKE_NVCC_COMPILER */
/* #undef KRIPKE_NVCC_FLAGS */

#endif
