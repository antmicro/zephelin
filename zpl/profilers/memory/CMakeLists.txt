# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

zephyr_library_sources_ifdef(
  CONFIG_ZPL_MEMORY_PROFILING
  memory_profiler.c
  memory_event.c
)
