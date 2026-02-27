# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)

set(DTC_OVERLAY_FILE "${CMAKE_CURRENT_SOURCE_DIR}/../../boards/max32650fthr.overlay")

set(SIGNAL_BASE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../optional/modules/lib/tflite-micro/signal")

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(app)

zephyr_library_include_directories(
    ${SIGNAL_BASE_DIR}/micro/kernels
    ${SIGNAL_BASE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/../data
)

zephyr_library_sources(
    ${SIGNAL_BASE_DIR}/micro/kernels/fft_auto_scale_kernel.cc
    ${SIGNAL_BASE_DIR}/micro/kernels/fft_auto_scale_common.cc
    ${SIGNAL_BASE_DIR}/micro/kernels/energy.cc
    ${SIGNAL_BASE_DIR}/micro/kernels/filter_bank.cc
    ${SIGNAL_BASE_DIR}/micro/kernels/filter_bank_log.cc
    ${SIGNAL_BASE_DIR}/micro/kernels/filter_bank_spectral_subtraction.cc
    ${SIGNAL_BASE_DIR}/micro/kernels/filter_bank_square_root.cc
    ${SIGNAL_BASE_DIR}/micro/kernels/filter_bank_square_root_common.cc
    ${SIGNAL_BASE_DIR}/micro/kernels/pcan.cc
    ${SIGNAL_BASE_DIR}/src/fft_auto_scale.cc
    ${SIGNAL_BASE_DIR}/src/energy.cc
    ${SIGNAL_BASE_DIR}/src/filter_bank.cc
    ${SIGNAL_BASE_DIR}/src/filter_bank_log.cc
    ${SIGNAL_BASE_DIR}/src/filter_bank_spectral_subtraction.cc
    ${SIGNAL_BASE_DIR}/src/filter_bank_square_root.cc
    ${SIGNAL_BASE_DIR}/src/pcan_argc_fixed.cc
    ${SIGNAL_BASE_DIR}/src/max_abs.cc
    ${SIGNAL_BASE_DIR}/src/msb_32.cc
    ${SIGNAL_BASE_DIR}/src/msb_64.cc
    ${SIGNAL_BASE_DIR}/src/log.cc
    ${SIGNAL_BASE_DIR}/src/square_root_32.cc
    ${SIGNAL_BASE_DIR}/src/square_root_64.cc
)

add_compile_definitions(IS_PREPROCESSOR)
target_sources(app PRIVATE src/main.cpp)

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../../../common/tflm ${CMAKE_CURRENT_BINARY_DIR}/tflm)
zephyr_link_libraries(tflm_model)
