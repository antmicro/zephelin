# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20)

zephyr_library_named(zpl)
zephyr_library_sources(zpl.c time.c)
zephyr_library_sources_ifdef(
  CONFIG_INSTRUMENTATION
  instr.c
)

add_subdirectory(profilers)
add_subdirectory(conf)
add_subdirectory(backends)
add_subdirectory(scopes)

if (CONFIG_INSTRUMENTATION AND NOT CONFIG_ZPL_INTERNALS_INSTRUMENTATION)
  file(GLOB_RECURSE sources RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}/.." "*.c" "*.cpp" "../include/*.h" "../include/**/*.h" "../include/**/*.hpp")
  string(REPLACE ";" "," sources "${sources}")
  if(CONFIG_INSTRUMENTATION_EXCLUDE_FILE_LIST STREQUAL "")
    set(CONFIG_INSTRUMENTATION_EXCLUDE_FILE_LIST "${sources}")
  else()
    set(CONFIG_INSTRUMENTATION_EXCLUDE_FILE_LIST "${CONFIG_INSTRUMENTATION_EXCLUDE_FILE_LIST},${sources}")
  endif()

  if(NOT CONFIG_INSTRUMENTATION_EXCLUDE_FILE_LIST STREQUAL "")
    message(STATUS "Excluding Zepheling files from instrumentation")
    zephyr_compile_options("-finstrument-functions-exclude-file-list=${CONFIG_INSTRUMENTATION_EXCLUDE_FILE_LIST}")
  endif()
endif()
