# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides a singleton class representing the state of Zephelin server.
"""

import asyncio
from typing import Optional


class StateManager:
    """
    Global state manager that should be used work with the application state.

    This class should not be imported directly, but rather
    `global_state` object should be imported to use this class.
    """

    def __init__(self):
        """
        Creates the state manager.
        """
        self.trace_active: bool = False
        self.read_task: Optional[asyncio.Task] = None


global_state = StateManager()
