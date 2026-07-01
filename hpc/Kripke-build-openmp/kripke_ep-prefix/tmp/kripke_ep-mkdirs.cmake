# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file LICENSE.rst or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION ${CMAKE_VERSION}) # this file comes with cmake

# If CMAKE_DISABLE_SOURCE_CHANGES is set to true and the source directory is an
# existing directory in our source tree, calling file(MAKE_DIRECTORY) on it
# would cause a fatal error, even though it would be a no-op.
if(NOT EXISTS "/home/drew/mantis-monitor/hpc/Kripke/cmake/kripke")
  file(MAKE_DIRECTORY "/home/drew/mantis-monitor/hpc/Kripke/cmake/kripke")
endif()
file(MAKE_DIRECTORY
  "/home/drew/mantis-monitor/hpc/Kripke-build-openmp/kripke-build"
  "/home/drew/mantis-monitor/hpc/Kripke-build-openmp/kripke_ep-prefix"
  "/home/drew/mantis-monitor/hpc/Kripke-build-openmp/kripke_ep-prefix/tmp"
  "/home/drew/mantis-monitor/hpc/Kripke-build-openmp/kripke_ep-prefix/src/kripke_ep-stamp"
  "/home/drew/mantis-monitor/hpc/Kripke-build-openmp/kripke_ep-prefix/src"
  "/home/drew/mantis-monitor/hpc/Kripke-build-openmp/kripke_ep-prefix/src/kripke_ep-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/drew/mantis-monitor/hpc/Kripke-build-openmp/kripke_ep-prefix/src/kripke_ep-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/drew/mantis-monitor/hpc/Kripke-build-openmp/kripke_ep-prefix/src/kripke_ep-stamp${cfgdir}") # cfgdir has leading slash
endif()
