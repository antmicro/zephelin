# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20)

zephyr_library_named(zpl)
zephyr_library_sources(zpl.c)

add_subdirectory(profilers)
add_subdirectory(conf)
add_subdirectory(backends)
add_subdirectory(scopes)
