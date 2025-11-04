# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

string(REPLACE "/" "_" board_sanitized "${BOARD}")

string(REPLACE "/" ";" board_list "${BOARD}")
list(GET board_list 0 board_short)

set(board_overlay "${CMAKE_CURRENT_LIST_DIR}/boards/${board_sanitized}.overlay")
set(board_short_overlay "${CMAKE_CURRENT_LIST_DIR}/boards/${board_short}.overlay")

if(EXISTS "${board_overlay}")
  set(EXTRA_DTC_OVERLAY_FILE "${board_overlay}" CACHE STRING "Auto-loaded board overlay")
elseif(EXISTS "${board_short_overlay}")
  set(EXTRA_DTC_OVERLAY_FILE "${board_short_overlay}" CACHE STRING "Auto-loaded board overlay")
endif()
