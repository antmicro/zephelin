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
import time
from pathlib import Path

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


def get_zephyr_chosen(chosen: str) -> str:
    """
    Retrieves Zephyr console UART from device tree.
    """
    with open("./build/zephyr/zephyr.dts") as dts_file:
        board_dts = dts_file.read()

    match = re.findall(rf"zephyr,{chosen} = &([a-zA-Z0-9]*);", board_dts, re.MULTILINE)
    if len(match):
        return match[0]

    raise Exception("Zephyr tracing UART not found")


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
    parser.add_argument(
        "--repl", type=Path, help="Path to board REPL, if not specified then default is used"
    )
    parser.add_argument("--sensor", type=str, help="DTS path to sensor, i.e. i2c1.lis2ds12")
    parser.add_argument("--sensor-samples", type=Path, help="Path to file with sensor samples")
    parser.add_argument("--trace-output", type=Path, help="Path to file where traces will be saved")
    parser.add_argument("--trace-output-stdout", action="store_true", help="Write trace to stdout")
    parser.add_argument(
        "--timeout", type=int, help="Defines for how long the simulation should run in seconds."
    )
    args = parser.parse_args()

    board = get_cmake_var("BOARD:STRING").split("/")[0]
    build_path = get_cmake_var("APPLICATION_BINARY_DIR:PATH")
    project_name = get_cmake_var("CMAKE_PROJECT_NAME:STATIC")

    emulation = Emulation()

    platform = emulation.add_mach(board)
    if args.repl is None:
        platform.load_repl(REPLS[board])
    else:
        platform.load_repl(str(args.repl.resolve()))

    platform.load_elf(f"{build_path}/zephyr/zephyr.elf")

    if args.debug:
        platform.StartGdbServer(3333)
        print("gdb server started at :3333")
        print("Press ENTER to start simulation")

        input()

    # create pty terminal for UART with traces
    trace_uart = get_zephyr_chosen("tracing-uart")
    emulation.CreateUartPtyTerminal("trace_uart_term", "/tmp/uart-trace")
    emulation.Connector.Connect(
        getattr(platform.sysbus, trace_uart).internal,
        emulation.externals.trace_uart_term,
    )

    trace_serial = serial.Serial("/tmp/uart-trace", baudrate=115200)

    # create pty terminal for UART with logs
    console_uart = get_zephyr_chosen("console")
    emulation.CreateUartPtyTerminal("console_uart_term", "/tmp/uart-log")
    emulation.Connector.Connect(
        getattr(platform.sysbus, console_uart).internal,
        emulation.externals.console_uart_term,
    )

    if console_uart != trace_uart:
        console_serial = serial.Serial("/tmp/uart-log", baudrate=115200)
        print(f"Writing console ({console_uart}) output to stdout")
    else:
        console_serial = None

    if args.sensor is not None:
        if args.sensor_samples is None:
            print("Missing sensor samples file")
            exit(1)

        sensor = platform.sysbus
        for node in args.sensor.split("."):
            sensor = getattr(sensor, node)

        if not hasattr(sensor, "FeedSample"):
            print(f"Sensor {args.sensor} is not supported")
            exit(1)

        if not args.sensor_samples.exists():
            print(f"File {args.sensor_samples} does not exist")
            exit(1)

        sensor.FeedSample(str(args.sensor_samples.resolve()), -1)

    if args.trace_output:
        trace_f = open(args.trace_output, "wb")
        print(f"Writing tracing-uart ({trace_uart}) output to {args.trace_output} file")
    else:
        trace_f = None

    print("Starting Renode simulation. Press CTRL+C to exit.")
    emulation.StartAll()

    simulation_start = time.time()
    while True:
        try:
            traces = trace_serial.read_all()
            if trace_f is not None:
                trace_f.write(traces)
            if args.trace_output_stdout:
                print(traces.decode(errors="ignore"), end="", flush=True)

            if console_serial is not None:
                logs = console_serial.read_all()
                print(logs.decode(errors="ignore"), end="", flush=True)

        except KeyboardInterrupt:
            break
        # pylint: disable-next=try-except-raise
        except Exception:
            print("Program failed, saving traces...")
            if trace_f is not None:
                trace_f.close()
            trace_serial.close()
            raise
        if args.timeout:
            if time.time() - simulation_start >= args.timeout:
                break

    if trace_f is not None:
        trace_f.close()

    trace_serial.close()
    emulation.clear()

    print("\nExiting...")
