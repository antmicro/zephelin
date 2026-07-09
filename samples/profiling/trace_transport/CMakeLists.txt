# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0


# Copied from ../tflm_instrumentation/CMakeLists.txt
cmake_minimum_required(VERSION 3.20.0)

include(${CMAKE_CURRENT_SOURCE_DIR}/../../common/instrumentation/boards.cmake)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(tensorflow_hello_world)

set(NO_THREADSAFE_STATICS $<TARGET_PROPERTY:compiler-cpp,no_threadsafe_statics>)
zephyr_compile_options($<$<COMPILE_LANGUAGE:CXX>:${NO_THREADSAFE_STATICS}>)

target_sources(app PRIVATE ../../profiling/tflm_instrumentation/src/main.cpp)

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../../common/tflm ${CMAKE_CURRENT_BINARY_DIR}/tflm)
target_link_libraries(app PRIVATE tflm_model)
