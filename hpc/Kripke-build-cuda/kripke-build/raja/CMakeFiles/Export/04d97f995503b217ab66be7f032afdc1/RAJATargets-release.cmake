#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "RAJA" for configuration "Release"
set_property(TARGET RAJA APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(RAJA PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CUDA"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libRAJA.a"
  )

list(APPEND _cmake_import_check_targets RAJA )
list(APPEND _cmake_import_check_files_for_RAJA "${_IMPORT_PREFIX}/lib/libRAJA.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
