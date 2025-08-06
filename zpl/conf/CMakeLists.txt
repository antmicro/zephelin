# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

zephyr_library_sources_ifdef(CONFIG_ZPL_RUNTIME_CONFIG_NONE configuration_none.c)
zephyr_library_sources_ifdef(CONFIG_ZPL_RUNTIME_CONFIG_UART configuration_uart.c)
zephyr_library_sources_ifdef(CONFIG_ZPL_RUNTIME_CONFIG_DEBUG configuration_debug.c)
