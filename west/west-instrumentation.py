# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0


"""ZPL West extension for instrumentation data capture."""

import importlib
import signal
import subprocess
import time
from copy import copy
from pathlib import Path
from textwrap import dedent

import serial
from utils import get_zephyr_elf, start_debugserver
from west.commands import WestCommand

west_zpl = importlib.import_module("west-zpl")


def get_stream(port):
    """
    Get a binary stream from target.

    This function gets a binary stream extracted from target connected via port
    'port' and returns the stream as 'bytes' object.
    """
    stream = b""
    while True:
        byte = port.read(1)
        stream = stream + byte
        if b"-*-#" in stream:  # Initiator
            stream = b""  # zero input buffer
            while True:
                byte = port.read(1)
                stream = stream + byte
                if b"-*-!" in stream:  # Terminator
                    stream = stream[:-4]  # trim terminator
                    return stream


class ZplInstrumentationUartCapture(WestCommand):
    """Main class for the zpl-instrumentation-uart-capture command."""

    def __init__(self):
        """Init function for the zpl-instrumentation-uart-capture command."""
        super().__init__(
            "zpl-instrumentation-uart-capture",
            "Capture instrumentation traces using UART",
            dedent("""
                Capture instrumentation traces using UART.

                This command captures traces using the serial interface."""),
        )

    def do_add_parser(self, parser_adder, parser=None, add_output=True):
        if parser is None:
            parser = parser_adder.add_parser(
                self.name, help=self.help, description=self.description
            )

        parser.add_argument("serial_port", help="Seral port")
        parser.add_argument("serial_baudrate", help="Seral baudrate")
        if add_output:
            parser.add_argument("output_path", help="Capture output path")

        return parser

    def do_run(self, args, unknown_args):
        ser = serial.serial_for_url(args.serial_port, args.serial_baudrate)
        if ser.is_open:
            self.inf(f"Capturing instrumentation traces on {ser.port}@{ser.baudrate}...")
        else:
            self.die(f"Couldn't open port {ser.port}!")

        ser.write("dump_trace\r".encode())

        with open(args.output_path, "wb") as f:
            stream = get_stream(ser)
            n = f.write(stream)
            self.inf(f"Wrote {n} bytes to {args.output_path}")

        ser.close()


class ZplInstrumentationUartGdbCapture(WestCommand):
    """Main class for the zpl-instrumentation-uart-gdb-capture command."""

    def __init__(self):
        """Init function for the zpl-instrumentation-uart-capture command."""
        super().__init__(
            "zpl-instrumentation-uart-gdb-capture",
            "Capture instrumentation traces via UART and Zephelin traces with GDB",
            dedent("""
                Capture instrumentation traces via UART and Zephelin traces with GDB.

                This command combines zpl-instrumentation-uart-capture and zpl-gdb-capture
                commands to capture instrumentation and Zephelin traces at the same time."""),
        )

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name, help=self.help, description=self.description)

        ZplInstrumentationUartCapture.do_add_parser(self, parser_adder, parser, False)
        west_zpl.ZplGdbCapture.do_add_parser(self, parser_adder, parser, False)

        parser.add_argument(
            "instr_output_path", help="Instrumentation capture output path", type=Path
        )
        parser.add_argument("output_path", help="Capture output path", type=Path)

        return parser

    def do_run(self, args, unknown_args):
        if args.gdb_port not in range(65536):
            self.die(f"The GDB port ({args.gdb_port}) is invalid. Should be a 0-65535 value.")

        if args.elf_path is None:
            elf = get_zephyr_elf()
            if elf is None:
                self.die("Cannot deduce Zephyr ELF path, please provide it with --elf-path")
            args.elf_path = elf

        proc_debugserver = None
        if not args.no_debug_server:
            self.inf(f"Setting up the debug server on port {args.gdb_port}...")
            self.inf("Waiting for the debugserver to start...")
            proc_debugserver = start_debugserver(args.gdb_port, args.openocd)
            if (ret_code := proc_debugserver.poll()) is not None:
                self.die(f"The debug server exited with code: {ret_code}")

        try:
            cmd_gdb = [
                args.gdb,
                "-batch",
                "-ex",
                "set pagination off",
                "-ex",
                f"target remote :{args.gdb_port}",
                "-ex",
                "continue",
                args.elf_path,
            ]
            proc_gdb = subprocess.Popen(cmd_gdb, stdout=subprocess.PIPE)
            # Wait for GDB to spawn and connect to the board
            time.sleep(2.0)
            if (ret_code := proc_gdb.poll()) is not None:
                self.die(f"GDB finished with code {ret_code}")

            original_output: Path = args.output_path

            args.output_path = str(args.instr_output_path)
            ZplInstrumentationUartCapture.do_run(self, args, unknown_args)
            proc_gdb.send_signal(signal.SIGINT)
            time.sleep(2.0)
            self.inf(f"GDB return code {proc_gdb.poll()}")

            args_gdb_capture = copy(args)
            args_gdb_capture.no_debug_server = True
            args_gdb_capture.output_path = str(original_output)

            west_zpl.ZplGdbCapture.do_run(self, args_gdb_capture, unknown_args)
        finally:
            if proc_debugserver and proc_debugserver.poll() is None:
                proc_debugserver.send_signal(signal.SIGINT)
