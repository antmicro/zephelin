# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Utilities for Zephelin West extension.
"""

import subprocess
import sys
import time
from argparse import ArgumentParser
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


def add_gdb_common_args(parser: ArgumentParser):
    """
    Adds common arguments required for GDB.
    """
    parser.add_argument(
        "--elf-path",
        help="Zephyr ELF path, by default deduced from Zephyr build dir",
        default=None,
    )
    parser.add_argument("--gdb-port", help="GDB server port", type=int, default=3333)
    parser.add_argument("--gdb", help="Path to GDB", type=str, default="gdb-multiarch")


def get_zephyr_elf():
    """
    Returns deduced Zephyr ELF path, based on Zephyr build directory.
    """
    build_dir = zephyr_build_dir()
    if build_dir is None or not (elf := build_dir / "zephyr" / "zephyr.elf").exists():
        return None
    return elf


def start_debugserver(gdb_port: int, openocd: Path | None = None) -> subprocess.Popen:
    """
    Starts a debugserver with specified port.
    """
    cmd_debugserver = f"west debugserver --gdb-port {gdb_port}".split()
    if openocd and openocd.exists():
        cmd_debugserver += ["--openocd", str(openocd.resolve())]
    proc_debugserver = subprocess.Popen(
        cmd_debugserver, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    time.sleep(2)
    return proc_debugserver


def get_kconfigs(build_dir: Path | None = None) -> dict[str, str | None]:
    """
    Returns configs used for the current build application.
    """
    if build_dir is None:
        build_dir = zephyr_build_dir()

    config_file = build_dir / "zephyr" / ".config"
    if not config_file.exists():
        return []

    with config_file.open("r") as fd:
        configs = fd.read()

    configs = [c for c in configs.splitlines() if "CONFIG_" in c]
    conf_val = {}
    for c_line in configs:
        if c_line.startswith("# ") and c_line.endswith(" is not set"):
            conf_val[c_line[2:-11]] = None
            continue
        if c_line.startswith("# "):
            continue
        c, val = c_line.split("=", 1)
        conf_val[c] = val

    return conf_val
