#!/usr/bin/env python3

# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Python script for running Kenning Zephyr Runtime in Renode.
"""

import argparse
import re

import serial
from pyrenode3.wrappers import Emulation


def get_cmake_var(cmake_var: str) -> str:
    """
    Retrieves variable from CMake cache.
    """
    with open("./build/CMakeCache.txt") as cache_file:
        cmake_cache = cache_file.read()

    match = re.findall(rf"^{cmake_var}=([^\n\t\s]*)", cmake_cache, re.MULTILINE)
    if len(match):
        return match[0]

    raise Exception(f"{cmake_var} variable not found in CMake cache")


def get_zephyr_console_uart(board: str) -> str:
    """
    Retrieves Zephyr console UART from device tree.
    """
    with open("./build/zephyr/zephyr.dts") as dts_file:
        board_dts = dts_file.read()

    match = re.findall(r"zephyr,console = &([a-zA-Z0-9]*);", board_dts, re.MULTILINE)
    if len(match):
        return match[0]

    raise Exception("Zephyr console UART not found")


ZEPHYR_DASHBOARD_URL = "https://zephyr-dashboard.renode.io/zephyr_sim/54b826336bae437f851fcba332481e24a7e1532d/0e512aebf21a8c51bda51fa67354277811f10a40"
REPLS = {
    "max32690fthr": f"{ZEPHYR_DASHBOARD_URL}/max32690fthr_max32690_m4/hello_world/hello_world.repl",
    "max78002evkit": f"{ZEPHYR_DASHBOARD_URL}/max78002evkit_max78002_m4/hello_world/hello_world.repl",  # noqa: E501
    "qemu_cortex_m3": f"{ZEPHYR_DASHBOARD_URL}/qemu_cortex_m3/hello_world/hello_world.repl",
    "stm32f429i_disc1": f"{ZEPHYR_DASHBOARD_URL}/stm32f429i_disc1/hello_world/hello_world.repl",
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__, allow_abbrev=False)
    parser.add_argument("--debug", action="store_true", help="Enable GDB server")
    args = parser.parse_args()

    board = get_cmake_var("BOARD:STRING").split("/")[0]
    build_path = get_cmake_var("APPLICATION_BINARY_DIR:PATH")
    project_name = get_cmake_var("CMAKE_PROJECT_NAME:STATIC")

    emulation = Emulation()

    platform = emulation.add_mach(board)
    platform.load_repl(REPLS[board])
    platform.load_elf(f"{build_path}/zephyr/zephyr.elf")

    if args.debug:
        platform.StartGdbServer(3333)
        print("gdb server started at :3333")
        print("Press ENTER to start simulation")

        input()

    # create pty terminal for UART with logs
    console_uart = get_zephyr_console_uart(board)
    emulation.CreateUartPtyTerminal("console_uart_term", "/tmp/uart-log")
    emulation.Connector.Connect(
        getattr(platform.sysbus, console_uart).internal,
        emulation.externals.console_uart_term,
    )

    console = serial.Serial("/tmp/uart-log", baudrate=115200)

    print("Starting Renode simulation. Press CTRL+C to exit.")
    emulation.StartAll()

    logs_tail = ""
    check_first = True
    with open("channel0_0", "wb") as out_fd:
        while True:
            try:
                logs = console.read_all()
                # print(logs.decode(errors="ignore"), end="", flush=True)
                out_fd.write(logs)
            except KeyboardInterrupt:
                print("Exiting...")
                break
            # pylint: disable-next=try-except-raise
            except Exception:
                raise

    console.close()
    emulation.clear()
