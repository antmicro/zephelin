# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(zpl_test)

target_sources(app PRIVATE src/main.c $ENV{ZPL_BASE}/zpl/backends/usb_backend.c)
zephyr_linker_sources(DATA_SECTIONS usbd_context.ld)
