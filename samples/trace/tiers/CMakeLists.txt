# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)

include(${CMAKE_CURRENT_SOURCE_DIR}/../common/boards.cmake)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(app)
target_sources(app PRIVATE ../common/src/tflm_inference.c)

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../common/tflm ${CMAKE_CURRENT_BINARY_DIR}/tflm)
zephyr_link_libraries(tflm_model)
