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

    match = re.findall(rf"zephyr,{chosen} = &?([a-zA-Z0-9]*);", board_dts, re.MULTILINE)
    if len(match):
        return match[0]

    raise Exception("Zephyr tracing UART not found")


CTF_TRACE_START_TAG = b"_zpl_ctf_start__"
ZEPHYR_DASHBOARD_URL = "https://zephyr-dashboard.renode.io/zephyr_sim/d90d71c42c6d3a81b10b17b5eb5ab3d686b7512f/58aef12522b98e26da67642f9935efa38b6369df"
REPO_ROOT = str(Path(__file__).parent.parent.resolve())
REPLS = {
    "max32690fthr": f"{ZEPHYR_DASHBOARD_URL}/max32690fthr_max32690_m4/hello_world/hello_world.repl",
    "max78002evkit": f"{ZEPHYR_DASHBOARD_URL}/max78002evkit_max78002_m4/hello_world/hello_world.repl",  # noqa: E501
    "qemu_cortex_m3": f"{ZEPHYR_DASHBOARD_URL}/qemu_cortex_m3/hello_world/hello_world.repl",
    "stm32f429i_disc1": f"{ZEPHYR_DASHBOARD_URL}/stm32f429i_disc1/hello_world/hello_world.repl",
    "mpfs_icicle": f"{REPO_ROOT}/samples/profiling/smp_tvm/boards/mpfs_icicle_polarfire_u54_smp.repl",  # noqa: E501
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__, allow_abbrev=False)
    parser.add_argument("--debug", action="store_true", help="Enable GDB server")
    parser.add_argument(
        "--debug-start-immediately",
        action="store_true",
        help="Do not wait for input after spawning GDB server",
    )
    parser.add_argument(
        "--repl", type=Path, help="Path to board REPL, if not specified then default is used"
    )
    parser.add_argument("--sensor", type=str, help="DTS path to sensor, i.e. i2c1.lis2ds12")
    parser.add_argument("--sensor-samples", type=Path, help="Path to file with sensor samples")
    parser.add_argument("--trace-output", type=Path, help="Path to file where traces will be saved")
    parser.add_argument("--trace-output-stdout", action="store_true", help="Write trace to stdout")
    parser.add_argument(
        "--simulation-only",
        help="Only runs the simulation, without capturing the output",
        action="store_true",
    )
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

    # create pty terminal for UART with traces
    trace_uart = None
    try:
        trace_uart = get_zephyr_chosen("tracing-uart")
        emulation.CreateUartPtyTerminal("trace_uart_term", "/tmp/uart-trace")
        emulation.Connector.Connect(
            getattr(platform.sysbus, trace_uart).internal,
            emulation.externals.trace_uart_term,
        )
    except Exception:
        if not args.simulation_only:
            # Tracing UART is not required for a simulation only run
            raise

    trace_serial = None
    if not args.simulation_only:
        trace_serial = serial.Serial("/tmp/uart-trace", baudrate=115200)

    # create pty terminal for UART with logs
    console_uart = get_zephyr_chosen("console")
    console_serial = None
    if console_uart != trace_uart:
        emulation.CreateUartPtyTerminal("console_uart_term", "/tmp/uart-log")
        emulation.Connector.Connect(
            getattr(platform.sysbus, console_uart).internal,
            emulation.externals.console_uart_term,
        )
        if not args.simulation_only:
            console_serial = serial.Serial("/tmp/uart-log", baudrate=115200)
        else:
            print(f"Writing console ({console_uart}) output to stdout")

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

    if args.debug:
        platform.StartGdbServer(3333)
        print("gdb server started at :3333")
        if not args.debug_start_immediately:
            print("Press ENTER to start simulation")
            inp = None
            try:
                inp = input()
            except EOFError:
                # Assuming the run_renode.py was used inside the script, waiting for 20s
                time.sleep(20)

    trace_idx = 0
    trace_buff = b""
    trace_written = False

    print("Starting Renode simulation. Press CTRL+C to exit.")
    emulation.StartAll()

    simulation_start = time.time()
    try:
        while True:
            if args.simulation_only:
                time.sleep(args.timeout if args.timeout else 30)
                if args.timeout:
                    break
                continue

            traces = trace_serial.read_all()
            if trace_f is not None:
                trace_buff += traces

                if CTF_TRACE_START_TAG in trace_buff:
                    tag_idx = trace_buff.index(CTF_TRACE_START_TAG)
                    trace_f.write(trace_buff[:tag_idx])
                    trace_written = tag_idx > 0
                    if trace_written:
                        # open new file only if there were any traces written to previous
                        trace_f.close()
                        output_path = args.trace_output.with_stem(
                            args.trace_output.stem + f"_{trace_idx}"
                        )
                        trace_f = open(output_path, "wb")
                        trace_idx += 1
                        trace_written = False

                    trace_buff = trace_buff[tag_idx + len(CTF_TRACE_START_TAG) :]

                elif len(trace_buff) > len(CTF_TRACE_START_TAG):
                    trace_f.write(trace_buff[: -len(CTF_TRACE_START_TAG)])
                    trace_buff = trace_buff[-len(CTF_TRACE_START_TAG) :]
                    trace_written = True

            if args.trace_output_stdout:
                print(traces.decode(errors="ignore"), end="", flush=True)

            if console_serial is not None:
                logs = console_serial.read_all()
                print(logs.decode(errors="ignore"), end="", flush=True)

            if args.timeout:
                if time.time() - simulation_start >= args.timeout:
                    raise KeyboardInterrupt

    except KeyboardInterrupt:
        if trace_f is not None:
            trace_f.write(trace_buff)
    except Exception:
        print("Program failed, saving traces...")
    finally:
        if trace_f is not None:
            trace_f.close()

        if console_serial is not None:
            console_serial.close()
        if trace_serial is not None:
            trace_serial.close()
        emulation.clear()

    print("\nExiting...")
