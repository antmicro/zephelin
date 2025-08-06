# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

zephyr_library_sources_ifdef(CONFIG_ZPL_TRACE_BACKEND_TRIVIAL_UART trivial_uart_backend.c)
zephyr_library_sources_ifdef(CONFIG_ZPL_TRACE_BACKEND_USB usb_backend.c)
