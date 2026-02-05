#!/usr/bin/env python3

# Copyright (c) 2025-2026 Analog Devices, Inc.
# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Python script for running Zephelin profiling.
"""

import argparse
import os
import re
import sys
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
    "max32650fthr": (
        f"{ZEPHYR_DASHBOARD_URL}/max32650fthr/hello_world/hello_world.repl",
        f"{REPO_ROOT}/samples/common/boards/max32650fthr_timer.repl",
    ),
    "max78002evkit": f"{ZEPHYR_DASHBOARD_URL}/max78002evkit_max78002_m4/hello_world/hello_world.repl",  # noqa: E501
    "qemu_cortex_m3": f"{ZEPHYR_DASHBOARD_URL}/qemu_cortex_m3/hello_world/hello_world.repl",
    "stm32f429i_disc1": (
        f"{ZEPHYR_DASHBOARD_URL}/stm32f429i_disc1/hello_world/hello_world.repl",
        f"{REPO_ROOT}/samples/common/boards/stm32f429i_disc1_timer.repl",
    ),
    "mpfs_icicle": f"{REPO_ROOT}/samples/profiling/smp_tvm/boards/mpfs_icicle_polarfire_u54_smp.repl",  # noqa: E501
}


class RenodeMachine:
    """
    Representation of a simulated machine.
    """

    def __init__(
        self,
        index: int,
        elf: Path,
        emulation: Emulation,
        board: str,
        args: argparse.Namespace,
        console_uart: str | None = None,
        trace_uart: str | None = None,
        repl: Path | None = None,
    ):
        """
        Initialize the machine.
        """
        self.index = index
        self.board = board
        self.name = f"mach_{index}_{board}"
        self.elfs = args.elfs

        self.mach = emulation.add_mach(self.name)

        if not self.mach:
            print("Machine could not be added to the emulation")
            exit(1)

        if repl:
            repl_path = str(repl.resolve())
        elif board in REPLS:
            repl_path = REPLS[board]
        else:
            repl_path = f"{board}.repl"
            print(f"[{board}] Could not determine REPL. Trying {board}.repl")

        if not isinstance(repl_path, (list, tuple)):
            paths_to_load = [repl_path]
        else:
            paths_to_load = repl_path

        for r in paths_to_load:
            if not r.startswith("http") and not Path(r).exists():
                print(f"Error: REPL file not found at {r}")
                exit(1)
            self.mach.load_repl(r)

        self.mach.load_elf(str(elf.resolve()))

        self.trace_buffer = b""
        self.trace_index = 0

        self.simulation_only = args.simulation_only

        self.shared_uart = (console_uart == trace_uart) and (console_uart is not None)

        self.trace_serial = self._setup_uart(emulation, trace_uart, "trace")
        self.console_serial = None

        self.trace_file = None
        self.filename = None

        if not self.shared_uart:
            self.console_serial = self._setup_uart(emulation, console_uart, "console")

        if self.simulation_only:
            if self.console_serial:
                self.console_serial.close()
            if self.trace_serial:
                self.trace_serial.close()
            self.console_serial = self.trace_serial = None
            self.trace_file = None
        else:
            base = Path(args.trace_output)
            if self.index == 0:
                self.filename = base
            else:
                self.filename = f"{base.stem}_{self.index}{base.suffix}"

            self.trace_file = open(self.filename, "wb")
            print(f"[{self.board}] Started initial trace: {self.filename}")

        if args.debug:
            port = 3333 + index
            try:
                self.mach.StartGdbServer(port, True, "all")
            except Exception as e:
                print(e)
                print(f"Problems with starting the GDB Server on port {port}.")
                sys.exit(1)

        if args.sensor and args.sensor_samples:
            self._setup_sensor(args.sensor, args.sensor_samples)

    def _setup_uart(self, emulation, uart_name, type_label):
        """
        Set up UART connection.
        """
        if not uart_name:
            return None
        pty = "/tmp/uart-log" if type_label == "console" else f"/tmp/uart-trace-{self.index}"
        terminal_name = f"{type_label}_term_{self.index}"
        if os.path.exists(pty):
            os.remove(pty)
        emulation.CreateUartPtyTerminal(terminal_name, pty, True)

        timeout = 5
        while not os.path.exists(pty) and timeout > 0:
            time.sleep(0.1)
            timeout -= 0.1

        if not os.path.exists(pty):
            print(f"Error: PTY {pty} was not created by Renode in time.")
            exit(1)

        uart = getattr(self.mach.sysbus, uart_name, None)
        if uart:
            emulation.Connector.Connect(
                uart.internal,
                getattr(emulation.externals, terminal_name),
            )
        else:
            print(f"Error: UART {uart_name} could not be found")
            exit(1)
        return serial.Serial(pty, baudrate=115200)

    def _setup_sensor(self, sensor_path, samples_path):
        """
        Set up Sensor node.
        """
        sensor_node = self.mach.sysbus
        for node in sensor_path.split("."):
            sensor_node = getattr(sensor_node, node, None)
            if not sensor_node:
                break

        if hasattr(sensor_node, "FeedSample") and Path(samples_path).exists():
            sensor_node.FeedSample(str(Path(samples_path).resolve()), -1)
            print(f"[{self.board}] Feeding samples to {sensor_path}")

    def process_data(self):
        """
        Handle console print and trace gathering from simulation run.
        """
        if self.simulation_only:
            return

        if self.console_serial and self.console_serial.in_waiting:
            try:
                logs = self.console_serial.read_all()
                print(f"[{self.board}-{self.index}] {logs.decode(errors='ignore')}")
            except Exception as e:
                print(f"[{self.board}-{self.index}] Error reading console {e}", file=sys.stderr)

        if self.trace_serial:
            try:
                new_traces = self.trace_serial.read_all()
                if self.trace_file:
                    self.trace_buffer += new_traces
                    self._handle_trace_rotation()
            except Exception as e:
                print(f"[{self.board}-{self.index}] Error reading trace Uart: {e}")

    def _handle_trace_rotation(self):
        if CTF_TRACE_START_TAG in self.trace_buffer:
            tag_idx = self.trace_buffer.index(CTF_TRACE_START_TAG)
            self.trace_file.write(self.trace_buffer[:tag_idx])

            if tag_idx > 0:
                self.trace_file.close()
                self.trace_index += 1

                if self.filename:
                    new_path = f"{self.filename}_{self.trace_index}"
                else:
                    new_path = f"trace_{self.board}.bin_{self.trace_index}"

                self.trace_file = open(new_path, "wb")

            self.trace_buffer = self.trace_buffer[tag_idx + len(CTF_TRACE_START_TAG) :]

        elif len(self.trace_buffer) > len(CTF_TRACE_START_TAG):
            safe_to_write = len(self.trace_buffer) - len(CTF_TRACE_START_TAG)
            self.trace_file.write(self.trace_buffer[:safe_to_write])
            self.trace_buffer = self.trace_buffer[safe_to_write:]

    def cleanup(self):
        if self.trace_file:
            if self.trace_buffer:
                self.trace_file.write(self.trace_buffer)
            self.trace_file.close()
        if self.console_serial:
            self.console_serial.close()
        if self.trace_serial:
            self.trace_serial.close()


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
    build_path = Path(get_cmake_var("APPLICATION_BINARY_DIR:PATH"))
    project_name = get_cmake_var("CMAKE_PROJECT_NAME:STATIC")
    elf_path = build_path / "zephyr" / "zephyr.elf"
    args.elfs = [elf_path]

    c_uart = get_zephyr_chosen("console")
    try:
        t_uart = get_zephyr_chosen("tracing-uart")
    except Exception:
        t_uart = None if args.simulation_only else sys.exit("Tracing UART missing")

    emulation = Emulation()

    machine = RenodeMachine(
        index=0,
        elf=elf_path,
        emulation=emulation,
        board=board,
        args=args,
        console_uart=c_uart,
        trace_uart=t_uart,
        repl=args.repl,
    )

    if args.debug:
        if not args.debug_start_immediately:
            print("Press ENTER to start simulation")
            inp = None
        try:
            inp = input()
        except EOFError:
            # Assuming the run_renode.py was used inside the script, waiting for 20s
            time.sleep(20)

    emulation.StartAll()
    start_time = time.time()

    try:
        while True:
            if args.simulation_only:
                time.sleep(args.timeout if args.timeout else 1)
                if args.timeout and (time.time() - start_time) > args.timeout:
                    break
                continue

            machine.process_data()
            if args.timeout and (time.time() - start_time) > args.timeout:
                break
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    except Exception as e:
        print(f"Program failed with error: {e}")
        print("Saving traces and exiting...")
    finally:
        machine.cleanup()
        emulation.clear()
        print("Exiting...")
