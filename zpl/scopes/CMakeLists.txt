# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

zephyr_library_sources_ifdef(
  CONFIG_ZPL_SCOPE_MARKING
  scope_marking.c
  scope_event.c
)
zephyr_linker_sources_ifdef(CONFIG_ZPL_SCOPE_MARKING DATA_SECTIONS code_scope.ld)
