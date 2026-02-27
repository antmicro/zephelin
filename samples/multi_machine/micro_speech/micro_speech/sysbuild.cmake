# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

include(${CMAKE_CURRENT_LIST_DIR}/../../../common/boards.cmake)

set(preprocessor_EXTRA_DTC_OVERLAY_FILE ${EXTRA_DTC_OVERLAY_FILE} CACHE STRING "Overlay for node 0")
set(micro_speech_EXTRA_DTC_OVERLAY_FILE ${EXTRA_DTC_OVERLAY_FILE} CACHE STRING "Overlay for node 1")

ExternalZephyrProject_Add(
    APPLICATION preprocessor
    SOURCE_DIR ${CMAKE_CURRENT_LIST_DIR}/../preprocessor
)
