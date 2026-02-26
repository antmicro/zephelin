# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

include(${CMAKE_CURRENT_LIST_DIR}/../../../common/boards.cmake)

set(node_0_EXTRA_DTC_OVERLAY_FILE ${EXTRA_DTC_OVERLAY_FILE} CACHE STRING "Overlay for node 0")
set(node_1_EXTRA_DTC_OVERLAY_FILE ${EXTRA_DTC_OVERLAY_FILE} CACHE STRING "Overlay for node 1")

ExternalZephyrProject_Add(
    APPLICATION node_1
    SOURCE_DIR ${CMAKE_CURRENT_LIST_DIR}/../node_1
)
