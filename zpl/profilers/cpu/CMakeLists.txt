# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

zephyr_library_sources_ifdef(CONFIG_ZPL_CPU_LOAD_PROFILING cpu_load.c)
zephyr_library_sources_ifdef(CONFIG_ZPL_DIE_TEMP_PROFILING die_temp.c)
