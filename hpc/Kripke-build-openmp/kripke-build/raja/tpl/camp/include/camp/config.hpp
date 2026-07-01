//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~//
// Copyright (c) 2018-25, Lawrence Livermore National Security, LLC
// and Camp project contributors. See the camp/LICENSE file for details.
//
// SPDX-License-Identifier: (BSD-3-Clause)
//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~//

// Define CAMP_CONFIG_OVERRIDE to change this on a per-file basis
#if !defined(CAMP_CONFIG_OVERRIDE)
#define CAMP_ENABLE_OPENMP
/* #undef CAMP_ENABLE_TARGET_OPENMP */
/* #undef CAMP_ENABLE_CUDA */
/* #undef CAMP_ENABLE_HIP */
/* #undef CAMP_ENABLE_SYCL */
/* #undef CAMP_WIN_STATIC_BUILD */
#endif

#define CAMP_VERSION_MAJOR 2025
#define CAMP_VERSION_MINOR 12
#define CAMP_VERSION_PATCH 0

#define CAMP_VERSION                                           \
  (CAMP_VERSION_MAJOR * 1000000) + (CAMP_VERSION_MINOR * 1000) \
      + (CAMP_VERSION_PATCH)

#if (defined(_WIN32) || defined(_WIN64)) && !defined(CAMP_WIN_STATIC_BUILD)
#ifdef CAMP_DLL_EXPORTS
#define CAMP_DLL_EXPORT __declspec(dllexport)
#else
#define CAMP_DLL_EXPORT __declspec(dllimport)
#endif
#else
#define CAMP_DLL_EXPORT
#endif
