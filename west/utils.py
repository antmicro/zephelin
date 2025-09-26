# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Utilities for Zephelin West extension.
"""

import sys
from pathlib import Path

from west.util import west_topdir


def zephyr_build_dir() -> Path | None:
    """
    Returns path to Zephyr build directory.
    """
    topdir = Path(west_topdir())
    old_sys_path = sys.path[:]
    try:
        # Extend PYTHONPATH with Zephyr West scripts directory
        # and import helper functions
        sys.path.insert(1, str((topdir / "zephyr" / "scripts" / "west_commands").resolve()))
        from build_helpers import find_build_dir

        build_dir = find_build_dir(None)
        return Path(build_dir) if build_dir else build_dir
    finally:
        sys.path = old_sys_path
