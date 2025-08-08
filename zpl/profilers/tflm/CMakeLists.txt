# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

zephyr_library_sources_ifdef(CONFIG_ZPL_TFLM_EVENTS tflm_event.c)
zephyr_library_sources_ifdef(CONFIG_ZPL_TFLM_PROFILER tflm_profiler.cpp)
