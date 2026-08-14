# Copyright (c) 2025-2026 Analog Devices, Inc.
# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0


"""ZPL West extension for instrumentation data capture."""

import importlib
import signal
import subprocess
import time
from pathlib import Path
from textwrap import dedent

import serial
from tqdm import tqdm
from utils import get_kconfigs, get_zephyr_elf, start_debugserver
from west.commands import WestCommand

west_zpl = importlib.import_module("west-zpl")

# Tags used by instrumentation subsystem
INSTR_INIT_TAG = b"-*-INSTR-INIT-*-\r\n"
INSTR_START_TAG = b"-*-#"
INSTR_END_TAG = b"-*-!\r\n"
# The size of one instrumentation event in bytes
INSTR_EVENT_SIZE = 54


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
        if INSTR_START_TAG in stream:  # Initiator
            stream = b""  # zero input buffer
            while True:
                byte = port.read(1)
                stream = stream + byte
                if INSTR_END_TAG in stream:  # Terminator
                    stream = stream[: -len(INSTR_END_TAG)]  # trim terminator
                    return stream


class ZplInstrumentationUartCapture(WestCommand):
    """Main class for the zpl-instrumentation-uart-capture command."""

    DUMP_TRACE_CMD = b"instr_dump_trace\r"
    DUMP_ON_FULL_CONF = "CONFIG_INSTRUMENTATION_MODE_CALLGRAPH_DUMP_ON_FULL"

    def __init__(self, *args):
        """Init function for the zpl-instrumentation-uart-capture command."""
        self._kconfigs = None
        if args:
            super().__init__(*args)
        else:
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

        parser.add_argument("serial_port", help="Serial port")
        parser.add_argument("serial_baudrate", help="Serial baudrate")
        if add_output:
            parser.add_argument("output_path", help="Capture output path", type=Path)
        parser.add_argument(
            "--timeout",
            help="Timeout for instrumentation message, if message is not received, "
            "the script asks for remaining data from buffer and finishes",
            type=int,
            default=None,
        )

        return parser

    def _init_serial_port(self, args):
        _serial = serial.serial_for_url(args.serial_port, args.serial_baudrate)
        if _serial.is_open:
            self.inf(f"Capturing instrumentation traces on {_serial.port}@{_serial.baudrate}...")
        else:
            self.die(f"Couldn't open port {_serial.port}!")
        return _serial

    def _do_run_manual(self, args, unknown_args):
        ser = self._init_serial_port(args)
        ser.write(self.DUMP_TRACE_CMD)

        with open(args.output_path, "wb") as f:
            stream = get_stream(ser)
            n = f.write(stream)
            self.inf(f"Wrote {n} bytes to {args.output_path}")

        ser.close()

    def _do_run_auto(self, args, unknown_args):
        uart = self._init_serial_port(args)
        trace_idx = 0
        buff = b""
        progress_bar = tqdm(unit="B", unit_scale=True)
        f = open(args.output_path, "wb")

        tqdm.write(f"Writing trace to {args.output_path}")

        # Whether instrumentation message is currently being sent
        instr_bin_msg = None
        should_end = False

        timeout = args.timeout
        last_instr_msg = time.time()

        def _handler(sig, frame):
            nonlocal should_end
            should_end = True
            tqdm.write(
                "SIGINT received, capturing will end when instrumentation message is processed"
            )

        signal.signal(signal.SIGINT, _handler)

        def process_buff():
            nonlocal instr_bin_msg
            nonlocal buff
            nonlocal last_instr_msg

            not_enough_data = False
            while not not_enough_data:
                if (instr_bin_msg is None or not instr_bin_msg) and INSTR_START_TAG in buff:
                    instr_bin_msg = True
                    tag_idx = buff.index(INSTR_START_TAG)
                    if tag_idx > 0:
                        tqdm.write(buff[:tag_idx].decode(errors="ignore"), end="")
                    buff = buff[tag_idx + len(INSTR_START_TAG) :]
                    last_instr_msg = time.time()

                elif (instr_bin_msg is None or instr_bin_msg) and INSTR_END_TAG in buff:
                    instr_bin_msg = False
                    tag_idx = buff.index(INSTR_END_TAG)
                    if INSTR_START_TAG in buff[:tag_idx]:
                        breakpoint()
                    f.write(buff[:tag_idx])
                    progress_bar.update(len(buff[:tag_idx]))
                    buff = buff[tag_idx + len(INSTR_END_TAG) :]

                elif len(buff) > len(INSTR_INIT_TAG):
                    if instr_bin_msg:
                        a = buff[: -len(INSTR_INIT_TAG)]
                        if INSTR_END_TAG in a or INSTR_START_TAG in a:
                            breakpoint()
                        f.write(a)
                        progress_bar.update(len(buff[: -len(INSTR_INIT_TAG)]))
                    elif instr_bin_msg is not None and len(buff) >= len(INSTR_INIT_TAG):
                        tqdm.write(buff[: -len(INSTR_INIT_TAG)].decode(errors="ignore"), end="")
                    buff = buff[-len(INSTR_INIT_TAG) :]

                else:
                    not_enough_data = True

        def ask_for_trace():
            uart.write(self.DUMP_TRACE_CMD)

            stream = get_stream(uart)
            # If size is smaller than one event, ignore the data
            # size based on sizeof(struct instr_record)
            if len(stream) < INSTR_EVENT_SIZE:
                return
            f.write(stream)

        try:
            while True:
                buff += uart.read_all()

                if INSTR_INIT_TAG in buff:
                    tag_idx = buff.index(INSTR_INIT_TAG)
                    process_buff()
                    f.close()
                    output_path = args.output_path.with_stem(
                        args.output_path.stem + f"_{trace_idx}"
                    )
                    tqdm.write(
                        f"\nFound instrumentation init tag, writing trace to new file {output_path}"
                    )
                    f = open(output_path, "wb")
                    buff = buff[tag_idx + len(INSTR_INIT_TAG) :]
                    progress_bar.reset()
                    progress_bar.update(len(buff))
                    trace_idx += 1
                    instr_bin_msg = False
                    continue
                process_buff()
                if timeout and last_instr_msg and time.time() - last_instr_msg >= timeout:
                    tqdm.write(
                        "\nInstrumentation message not received within "
                        f"last {timeout} seconds, finishing"
                    )
                    # Get remaining data from the instrumentation buffer
                    ask_for_trace()
                    break
                # Quit if SIGINT was received and instrumentation message is not being processed
                if should_end and not instr_bin_msg:
                    # Buffer was not filled, get data from it
                    if last_instr_msg is None:
                        ask_for_trace()
                    break
        finally:
            f.close()
            uart.close()
            progress_bar.close()

    def get_kconfigs(self):
        if self._kconfigs is None:
            self._kconfigs = get_kconfigs()
        return self._kconfigs

    def do_run(self, args, unknown_args):
        confs = self.get_kconfigs()
        if confs.get(self.DUMP_ON_FULL_CONF, None) == "y":
            self._do_run_auto(args, unknown_args)
        else:
            self._do_run_manual(args, unknown_args)


class ZplInstrumentationUartGdbCapture(ZplInstrumentationUartCapture):
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
        parser.add_argument(
            "instr_output_path", help="Instrumentation capture output path", type=Path
        )
        parser.add_argument("output_path", help="Capture output path", type=Path)
        west_zpl.add_gdb_common_args(parser)
        parser.add_argument(
            "--no-debug-server", help="Don't set up the debug server", action="store_true"
        )
        parser.add_argument("--openocd", help="Path to custom OpenOCD", type=Path, default=None)
        parser.add_argument(
            "--send-to-remote", help="Stream captured data to a remote socket", default=None
        )
        parser.add_argument(
            "--capture-once", help="Dump data from buffer only once and exit", action="store_true"
        )
        stop_condition_group = parser.add_mutually_exclusive_group()
        stop_condition_group.add_argument(
            "--buffer-full",
            help="Run application until trace buffer is full; works only with --capture-once",
            action="store_true",
        )
        stop_condition_group.add_argument(
            "--n-bytes",
            help="Run application until there is at least n in trace buffer;"
            " works only with --capture-once",
            type=int,
        )

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

        conf = self.get_kconfigs()
        dump_on_full = conf.get(self.DUMP_ON_FULL_CONF, None) == "y"
        try:
            cmd_gdb = [
                args.gdb,
                "-batch",
                "-ex",
                "set pagination off",
                "-ex",
                f"target remote :{args.gdb_port}",
                # Add sleep so that app is started after the UART capture is running
                *(["-ex", "shell sleep 5s"] if dump_on_full else []),
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

            args.output_path = args.instr_output_path
            ZplInstrumentationUartCapture.do_run(self, args, unknown_args)
            proc_gdb.send_signal(signal.SIGINT)
            time.sleep(2.0)
            self.inf(f"GDB return code {proc_gdb.poll()}")

            self.inf(f"Capturing traces to {original_output}...")

            if args.gdb_port not in range(65536):
                self.die(f"The GDB port ({args.gdb_port}) is invalid. Should be a 0-65535 value.")

            if args.elf_path is None:
                elf = get_zephyr_elf()
                if elf is None:
                    self.die("Cannot deduce Zephyr ELF path, please provide it with --elf-path")
                args.elf_path = elf

            cmd_gdb = [
                args.gdb,
                "-batch",
                "-ex",
                f"source {str(west_zpl.ZplGdbCapture.script_file)}",
                "-ex",
                f"target remote :{args.gdb_port}",
            ]

            if args.buffer_full:
                cmd_gdb += ["-ex", "wait_buffer_full"]
            elif args.n_bytes:
                cmd_gdb += ["-ex", f"wait_n_bytes {args.n_bytes}"]

            cmd_gdb += [
                "-ex",
                "calculate_start_end",
                "-ex",
                f"dump binary memory {original_output} $start $end",
                "-ex",
                "quit",
                args.elf_path,
            ]

            if original_output.exists():
                original_output.unlink()

            self.inf("Saving traces...")
            proc_gdb = subprocess.Popen(cmd_gdb, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            (output, _) = proc_gdb.communicate()
            exit_code = proc_gdb.wait()

            if exit_code != 0:
                if output:
                    self.err(output)
                self.die("Failed to capture tracing data!")

            self.inf("Processing CTF start tag...")
            with open(original_output, mode="r+b") as file:
                traces = file.read()
                file.truncate(0)
                file.seek(0)
                if west_zpl._CTF_TRACE_START_TAG in traces:
                    tag_idx = traces.index(west_zpl._CTF_TRACE_START_TAG)
                    traces = traces[tag_idx + len(west_zpl._CTF_TRACE_START_TAG) :]
                file.write(traces)

            self.inf("Done.")

        finally:
            if proc_debugserver and proc_debugserver.poll() is None:
                proc_debugserver.send_signal(signal.SIGINT)
