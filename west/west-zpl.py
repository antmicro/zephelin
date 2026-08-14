# Copyright (c) 2025-2026 Analog Devices, Inc.
# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Zephelin West extension for tracing data capture."""

import re
import signal
import socket
import subprocess
import tempfile
import threading
import time
from argparse import ArgumentParser
from pathlib import Path
from textwrap import dedent
from typing import Optional

import serial
import usb.core
import usb.util
from tqdm import tqdm
from utils import add_gdb_common_args, get_kconfigs, get_zephyr_elf, start_debugserver
from west.commands import WestCommand

_CTF_TRACE_START_TAG = b"_zpl_ctf_start__"

BYTES_IN_KILOBYTE = 1024


class CtfFileHandler:
    """
    Universal class, that manages CTF file juggling based on the
    '_zpl_ctf_start__' tags. Everything before the first passed tag is ignored.
    """

    def __init__(self, path: Path):
        """
        Initializes the class.

        Parameters
        ----------
        path: Path
            Path to the file, that the traces are to be saved to. If the file
            exists, it will be overriden. Everything after the first tag
            ('_zpl_ctf_start__') will be written to this file. Everything
            after subsequent tags will be written into other files (with '_1',
            '_02' etc. suffix added to the file name).
        """
        self.file_number = -1
        self.output_path = path
        self.sliding_window_chunk_buffer = b""
        self.current_output_path = path
        if path.exists():
            path.unlink()

    def _save_integral_chunk(self, chunk: bytes):
        """
        Takes the data stream piece by piece, and splits it into files based on
        tags.

        NOTE: This method assumes, that no tag is split between multiple
        pieces (chunks).

        Parameters
        ----------
        chunk: bytes
            Piece of the captured trace data.
        """
        if _CTF_TRACE_START_TAG in chunk:
            tag_idx = chunk.index(_CTF_TRACE_START_TAG)
            previous_file_chunk_part = chunk[:tag_idx]
            chunk = chunk[tag_idx + len(_CTF_TRACE_START_TAG) :]
            if self.file_number >= 0:
                with open(self.current_output_path, "ab") as of:
                    of.write(previous_file_chunk_part)
            self.file_number += 1
            if self.file_number == 0:
                self.current_output_path = self.output_path
            else:
                self.output_path.with_stem(self.output_path.stem + f"_{self.file_number}")
            if self.current_output_path.exists():
                self.current_output_path.unlink()
            tqdm.write(
                f"Found CTF trace start, writing trace to new file {self.current_output_path}"
            )
        if self.file_number >= 0:
            with open(self.current_output_path, "ab") as of:
                of.write(chunk)

    def save_chunk(self, chunk: bytes):
        """
        Takes the data stream piece by piece, and splits it into files based on
        tags.

        This method allows tags to be split between multiple pieces (chunks),
        and handles it with a sliding window chunk stored in an intermediate
        buffer. This buffer needs to be flushed by calling the 'close' method
        at the end of trace capture.

        Parameters
        ----------
        chunk: bytes
            Piece of the captured trace data.
        """
        # Ignore empty chunks
        if len(chunk) == 0:
            return
        joined_chunk = self.sliding_window_chunk_buffer + chunk
        # If the stored sliding window chunk is too small to ensure that no start tag
        # is missed - enlarge it.
        if len(self.sliding_window_chunk_buffer) < (len(_CTF_TRACE_START_TAG) - 1):
            self.sliding_window_chunk_buffer = joined_chunk
            return
        # If the tag is found between chunks, adjust chunk boundary to correct it.
        if (
            (_CTF_TRACE_START_TAG not in self.sliding_window_chunk_buffer)
            and (_CTF_TRACE_START_TAG not in chunk)
            and (_CTF_TRACE_START_TAG in joined_chunk)
        ):
            tag_idx = joined_chunk.index(_CTF_TRACE_START_TAG)
            self.sliding_window_chunk_buffer = joined_chunk[:tag_idx]
            chunk = joined_chunk[tag_idx:]
        # At this point we know for sure, that no tag is split between chunks.
        self._save_integral_chunk(self.sliding_window_chunk_buffer)
        # Our entire sliding window chunk is being processed, and the un-processed new
        # chunk becomes the new sliding window chunk.
        self.sliding_window_chunk_buffer = chunk

    def close(self):
        """
        Finalizes the work of the handler. Flushes the intermediate buffer,
        ensuring that the final sliding window chunk is processed.
        """
        if len(self.sliding_window_chunk_buffer) > 0:
            self._save_integral_chunk(self.sliding_window_chunk_buffer)


class ZplGdbCapture(WestCommand):
    """Main class for the zpl-gdb-capture command."""

    script_file = (Path(__file__).parent / "scripts.gdb").resolve()

    def __init__(self):
        """Init function for the zpl-gdb-capture command."""
        super().__init__(
            "zpl-gdb-capture",
            "Capture traces using GDB",
            dedent("""
                Capture traces using GDB.

                This command captures traces using GDB from RAM using the `dump` command."""),
        )

    def do_add_parser(self, parser_adder, parser=None, add_output=True):
        if parser is None:
            parser: ArgumentParser = parser_adder.add_parser(
                self.name, help=self.help, description=self.description
            )
        if add_output:
            parser.add_argument(
                "output_path", help="Capture output path", nargs="?", default=None, type=Path
            )

        add_gdb_common_args(parser)
        parser.add_argument(
            "--no-debug-server", help="Don't set up the debug server", action="store_true"
        )
        parser.add_argument("--openocd", help="Path to custom OpenOCD", type=Path, default=None)
        parser.add_argument(
            "--send-to-remote", help="Stream captured data to a remote socket", default=None
        )
        parser.add_argument(
            "--trace-processing-throttling-delay",
            help="Delay (in miliseconds) in the loop that processes/sends captured traces",
            type=int,
            default=1000,
        )
        parser.add_argument(
            "--capture-once", help="Dump data from buffer only once and exit", action="store_true"
        )
        parser.add_argument(
            "--measure-throughput",
            help="Display maximum trace gathering speed on shutdown (for continuous tracing)",
            default=False,
            action="store_true",
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

    def _cleanup_temp(self, path):
        if path:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass

    def do_run(self, args, unknown_args):
        if args.output_path is None and not args.send_to_remote:
            self.die("Output path is required unless --send-to-remote is used")

        if args.output_path:
            self.inf(f"Capturing traces to {args.output_path}...")

        if args.gdb_port not in range(65536):
            self.die(f"The GDB port ({args.gdb_port}) is invalid. Should be a 0-65535 value.")

        if args.elf_path is None:
            elf = get_zephyr_elf()
            if elf is None:
                self.die("Cannot deduce Zephyr ELF path, please provide it with --elf-path")
            args.elf_path = elf

        if not args.no_debug_server:
            self.inf(f"Setting up the debug server on port {args.gdb_port}...")
            self.inf("Waiting for the debugserver to start...")
            proc_debugserver = start_debugserver(args.gdb_port, args.openocd)
            if (ret_code := proc_debugserver.poll()) is not None:
                self.die(f"The debug server exited with code: {ret_code}")

        # Prepare GDB command
        cmd_prefix = [
            args.gdb,
            "-batch",
            "-ex",
            f"source {str(ZplGdbCapture.script_file)}",
            "-ex",
            f"target remote :{args.gdb_port}",
        ]
        cmd_gdb = cmd_prefix[:]

        _temp_path = tempfile.mktemp(prefix="zpl_trace_")
        Path(_temp_path).touch()

        gdb_logfile = tempfile.NamedTemporaryFile().name if args.measure_throughput else "/dev/null"

        if args.capture_once:
            if args.buffer_full:
                cmd_gdb += ["-ex", "wait_buffer_full"]
            elif args.n_bytes:
                cmd_gdb += ["-ex", f"wait_n_bytes {args.n_bytes}"]

            cmd_gdb += [
                "-ex",
                "calculate_start_end",
                "-ex",
                f"dump binary memory {_temp_path} $start $end",
            ]
        else:
            kconfigs = get_kconfigs()
            buffer_size = kconfigs.get("CONFIG_RAM_TRACING_BUFFER_SIZE", None)
            if buffer_size is None:
                self.wrn("CONFIG_RAM_TRACING_BUFFER_SIZE not found, using 1024 as the buffer size")
                buffer_size = "1024"
            cmd_gdb += [
                "-ex",
                f"dump_data_to_file {_temp_path} {buffer_size} {gdb_logfile}",
            ]
        cmd_gdb += [
            "-ex",
            "quit",
            args.elf_path,
        ]

        # Gather info about output file
        temp_file = Path(_temp_path)
        original_mtime = 0
        output_last_size = 0
        stats = temp_file.stat()
        original_mtime = stats.st_mtime
        file_handler = None
        if args.output_path:
            file_handler = CtfFileHandler(args.output_path)
        remote_socket = None
        if args.send_to_remote:
            remote_socket = _open_socket(self, args.send_to_remote)
            remote_socket.sendall(_CTF_TRACE_START_TAG)

        self.inf("Saving traces...")
        proc_gdb = subprocess.Popen(cmd_gdb, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if args.capture_once:
            # Capture data and wait for GDB to exit
            (output, _) = proc_gdb.communicate()
            exit_code = proc_gdb.wait()

            if exit_code == 0 and remote_socket:
                try:
                    with open(temp_file, "rb") as tf:
                        buf = tf.read()
                        if remote_socket:
                            remote_socket.sendall(buf)
                        if file_handler:
                            file_handler.save_chunk(buf)
                except Exception as e:
                    self.wrn(f"Failed to send data: {e}")
                finally:
                    remote_socket.close()
        else:
            # Monitor the output file and report its size
            stats = temp_file.stat()
            progress_bar = tqdm(unit="B", unit_scale=True)
            total_processing_time_seconds = 0
            total_processing_time_seconds_with_delay = 0
            try:
                tqdm.write("Press C-c to stop.")
                while True:
                    start_time = time.time()
                    stats = temp_file.stat()
                    size_diff = stats.st_size - output_last_size
                    if stats.st_mtime > original_mtime and size_diff > 0:
                        try:
                            with open(temp_file, "rb") as tf:
                                tf.seek(output_last_size)
                                chunk = tf.read(size_diff)
                                if remote_socket:
                                    remote_socket.sendall(chunk)
                                if file_handler:
                                    file_handler.save_chunk(chunk)
                        except Exception as e:
                            self.wrn(f"Failed to send data {e}")
                            if remote_socket:
                                remote_socket.close()
                                remote_socket = None
                        progress_bar.update(size_diff)
                        output_last_size = stats.st_size
                    total_processing_time_seconds = time.time() - start_time
                    time.sleep(args.trace_processing_throttling_delay / 1000)
                    total_processing_time_seconds_with_delay = time.time() - start_time

            except KeyboardInterrupt:
                # Stop running GDB
                proc_gdb.send_signal(signal.SIGINT)
                try:
                    proc_gdb.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc_gdb.kill()
                # Capture data that remains in the RAM buffer
                cmd_gdb = cmd_prefix + [
                    "-ex",
                    "calculate_start_end",
                    "-ex",
                    f"append binary memory {_temp_path} $start $end",
                ]
                tqdm.write("Saving remaining traces...")
                proc_gdb = subprocess.Popen(cmd_gdb, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                proc_gdb.communicate()
                proc_gdb.wait()
                size_diff = temp_file.stat().st_size - output_last_size
                stats = temp_file.stat()
                size_diff = stats.st_size - output_last_size
                if size_diff > 0:
                    try:
                        with open(temp_file, "rb") as tf:
                            tf.seek(output_last_size)
                            chunk = tf.read(size_diff)
                            if remote_socket:
                                remote_socket.sendall(chunk)
                            if file_handler:
                                file_handler.save_chunk(chunk)
                    except Exception:
                        pass
                # If mtime is newer, then part of a trace was captured
                exit_code = int(not (stats and stats.st_mtime > original_mtime))
            finally:
                progress_bar.close()
                if remote_socket:
                    remote_socket.close()
                if file_handler:
                    file_handler.close()
                if args.measure_throughput:
                    bytes = 0
                    seconds = 0
                    with open(gdb_logfile, "r") as file:
                        gdb_logs = file.readlines()
                        hex_regex = re.compile("0x[0-9a-f]+ ")
                        i = 0
                        while i < len(gdb_logs):
                            if "save_time" not in gdb_logs[i]:
                                i += 1
                                continue
                            seconds += float(gdb_logs[i].rsplit(":")[-1])
                            hex_base = 16
                            start = int(hex_regex.findall(gdb_logs[i + 1])[0], hex_base)
                            end = int(hex_regex.findall(gdb_logs[i + 2])[0], hex_base)
                            bytes += end - start
                            i += 3
                    gdb_logfile.unlink()
                    self.inf(f"Actual GDB trace dumping speed: {(bytes / seconds) / 1024}kB/s")
                    no_delay_rate = stats.st_size / total_processing_time_seconds
                    no_delay_rate = no_delay_rate / BYTES_IN_KILOBYTE
                    actual_rate = stats.st_size / total_processing_time_seconds_with_delay
                    actual_rate = actual_rate / BYTES_IN_KILOBYTE
                    self.inf(
                        f"Theoretical maximum trace file processing speed: {no_delay_rate}kB/s"
                    )
                    self.inf(
                        "Actual trace file processing speed (with"
                        f" throttling delays): {actual_rate}kB/s"
                    )

        if exit_code != 0:
            if output:
                self.err(output)
            self.die("Failed to capture tracing data!")

        self.inf("Done.")
        if _temp_path:
            try:
                Path(_temp_path).unlink(missing_ok=True)
            except OSError:
                pass

        if not args.no_debug_server:
            self.inf("Stopping the debugserver...")
            proc_debugserver.send_signal(signal.SIGINT)


class SerialWrapper:
    """Wrapper for serial port used for Socket passthrough."""

    def __init__(self, ser, socket_forward=False, socket_port=0):
        """Init SerialWrapper for a provided serial port."""
        self._ser = ser
        self._socket_forward = socket_forward

        self._ser_lock = threading.Lock()
        self._client_socket = None

        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._server_socket.bind(("127.0.0.1", socket_port))
        self._server_socket.listen(1)

        try:
            address = "socket://{}:{}".format(*self._server_socket.getsockname())
            print(f"Connect zaru.py to {address}")
        except OSError:
            pass

        threading.Thread(target=self._accept_loop, daemon=True).start()
        threading.Thread(target=self._write_loop, daemon=True).start()

    def _accept_loop(self):
        """Listen for incoming socket connections."""
        while True:
            try:
                conn, addr = self._server_socket.accept()

                if self._client_socket is not None:
                    print(f"Rejected connection from {addr}.")
                    conn.close()
                    continue

                self._client_socket = conn
                print(f"Client {addr} connected.")
            except OSError:
                break

    def _write_loop(self):
        """Read data from the socket and write it to the serial port."""
        while True:
            if not self._client_socket:
                time.sleep(0.01)
                continue

            try:
                data = self._client_socket.recv(1024)
                if data:
                    with self._ser_lock:
                        self._ser.write(data)
                else:
                    self._client_socket = None
            except OSError:
                self._client_socket = None

    def write(self, data):
        with self._ser_lock:
            self._ser.write(data)

    def read(self, size):
        with self._ser_lock:
            data = self._ser.read(size)

        if self._socket_forward and data and self._client_socket:
            try:
                self._client_socket.sendall(data)
            except OSError:
                pass

        return data

    def read_all(self):
        if self._ser.in_waiting == 0:
            time.sleep(0.001)
            return b""

        with self._ser_lock:
            data = self._ser.read_all()

        if self._socket_forward and data and self._client_socket:
            try:
                self._client_socket.sendall(data)
            except OSError:
                pass

        return data


class ZplUartCapture(WestCommand):
    """Main class for the zpl-uart-capture command."""

    def __init__(self):
        """Init function for the zpl-uart-capture command."""
        super().__init__(
            "zpl-uart-capture",
            "Capture traces using UART",
            dedent("""
                Capture traces using UART.

                This command captures traces using the serial interface."""),
        )

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name, help=self.help, description=self.description)

        parser.add_argument("serial_port", help="Seral port")
        parser.add_argument("serial_baudrate", help="Seral baudrate")
        parser.add_argument(
            "output_path", help="Capture output path", type=Path, nargs="?", default=None
        )
        parser.add_argument(
            "--send-to-remote", help="Stream captured data to a remote socket", default=None
        )
        parser.add_argument(
            "--send-enable",
            action="store_true",
            help=(
                "Send 'enable' to device before collecting data to enable tracing, requires "
                "CONFIG_TRACING_HANDLE_HOST_CMD to be enabled in the app"
            ),
        )
        parser.add_argument(
            "--socket-forward",
            action="store_true",
        )
        parser.add_argument(
            "--socket-port", type=int, default=0, help="Specific port to bind the TCP server to"
        )

        return parser

    def do_run(self, args, unknown_args):
        ser = serial.Serial(args.serial_port, args.serial_baudrate)
        if ser.is_open:
            self.inf(f"Capturing traces on {ser.port}@{ser.baudrate}...")
            self.inf("Press C-c to stop.")
        else:
            self.die(f"Couldn't open port {ser.port}!")

        serw = SerialWrapper(
            ser=ser,
            socket_forward=args.socket_forward,
            socket_port=args.socket_port,
        )

        remote_socket = None
        if args.send_to_remote:
            remote_socket = _open_socket(self, args.send_to_remote)

        file_handler = None
        if args.output_path:
            file_handler = CtfFileHandler(args.output_path)
            tqdm.write(f"Writing trace to {args.output_path}")

        progress_bar = tqdm(unit="B", unit_scale=True)

        data = b""

        if args.send_enable:
            ser.write(b"enable\r\n")
            tqdm.write("Sent b'enable'")
        try:
            while True:
                data = serw.read_all()
                progress_bar.update(len(data))
                if remote_socket:
                    try:
                        remote_socket.sendall(data)
                    except Exception as e:
                        self.wrn(f"Failed to send data: {e}")
                        remote_socket.close()
                        remote_socket = None
                if file_handler:
                    file_handler.save_chunk(data)
        except KeyboardInterrupt:
            if file_handler:
                file_handler.save_chunk(data)
        finally:
            ser.close()
            progress_bar.close()
            if remote_socket:
                remote_socket.close()
            if file_handler:
                file_handler.close()


class ZplUsbCapture(WestCommand):
    """Main class for the zpl-usb-capture command."""

    def __init__(self):
        """Init function for the zpl-usb-capture command."""
        super().__init__(
            "zpl-usb-capture",
            "Capture traces using usb",
            dedent("""
                Capture traces using USB.

                This command captures traces using USB."""),
        )

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name, help=self.help, description=self.description)

        parser.add_argument("vendor_id", help="Vendor ID")
        parser.add_argument("product_id", help="Product ID")
        parser.add_argument("output_path", help="Capture output path", nargs="?", default=None)
        parser.add_argument(
            "--send-to-remote", help="Stream captured data to a remote socket", default=None
        )
        parser.add_argument(
            "-t", "--timeout", help="Timeout of the USB capture in seconds", type=int, default=0
        )
        parser.add_argument(
            "-w",
            "--wait-for-device",
            help="When this flag is set, the command will wait for the device to connect",
            action="store_true",
            required=False,
        )

        return parser

    def do_run(self, args, unknown_args):
        vid = int(args.vendor_id, 16)
        pid = int(args.product_id, 16)
        dev = usb.core.find(idVendor=vid, idProduct=pid)

        if args.wait_for_device and dev is None:
            self.inf(f"Waiting for device {vid:04x}:{pid:04x}...")
            while (dev := usb.core.find(idVendor=vid, idProduct=pid)) is None:
                time.sleep(0.05)

        if dev is None:
            self.die(f"Couldn't open USB device with vid={vid} pid={pid}!")
        else:
            self.inf(f"Capturing traces from USB device {args.vendor_id}:{args.product_id}...")
            self.inf("Press C-c to stop.")

        # get the USB device interface
        dev.set_configuration()
        cfg = dev.get_active_configuration()
        intf = cfg[(0, 0)]
        usb.util.claim_interface(dev, intf)

        read_ep = usb.util.find_descriptor(
            intf,
            custom_match=lambda x: usb.util.endpoint_direction(x.bEndpointAddress)
            == usb.util.ENDPOINT_IN,
        )

        write_ep = usb.util.find_descriptor(
            intf,
            custom_match=lambda x: usb.util.endpoint_direction(x.bEndpointAddress)
            == usb.util.ENDPOINT_OUT,
        )
        write_ep.write("enable")
        progress_bar = tqdm(unit="B", unit_scale=True)

        remote_socket = None
        if args.send_to_remote:
            remote_socket = _open_socket(self, args.send_to_remote)
            if remote_socket:
                remote_socket.sendall(_CTF_TRACE_START_TAG)

        if args.output_path:
            f = open(args.output_path, "wb")
        else:
            f = None

        buf = usb.util.create_buffer(10 * 1024)
        while True:
            try:
                n_bytes = read_ep.read(buf, args.timeout * 1000)
                chunk = buf[:n_bytes]
                if remote_socket:
                    try:
                        remote_socket.sendall(chunk)
                    except Exception as e:
                        self.wrn(f"Failed to send data: {e}")
                        remote_socket.close()
                        remote_socket = None

                if f:
                    f.write(chunk)
                progress_bar.update(n_bytes)
            except usb.core.USBTimeoutError:
                self.die("USB operation timeout!")
            except KeyboardInterrupt:
                break
        if remote_socket:
            remote_socket.close()
        if f:
            f.close()


class ZplDebugConfig(WestCommand):
    """Main class for the zpl-debug-config command."""

    def __init__(self):
        """Init function for the zpl-debug-config command."""
        super().__init__(
            "zpl-debug-config",
            "Enable/Disable configs in runtime using debug interface.",
            dedent("""
                Enable/Disable configs in runtime using debug interface.

                This command can list available configs and enable/disable them."""),
        )

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name, help=self.help, description=self.description)

        parser.add_argument("config", help="Config to set")
        parser.add_argument("value", help="Value of the config (enable/disable)")
        add_gdb_common_args(parser)

        return parser

    def do_run(self, args, unknown_args):
        self.inf(f"Setting {args.config} config to {args.value}")

        if args.elf_path is None:
            elf = get_zephyr_elf()
            if elf is None:
                self.die("Cannot deduce Zephyr ELF path, please provide it with --elf-path")
            args.elf_path = elf

        cmd = [
            args.gdb,
            "-batch",
            "-ex",
            "set pagination off",
            "-ex",
            f"target remote :{args.gdb_port}",
            "-ex",
            f"set var debug_configs.{args.config} = {1 if args.value == 'enable' else 0}",
            "-ex",
            "quit",
            args.elf_path,
        ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        (output, _) = proc.communicate()
        exit_code = proc.wait()

        if exit_code != 0:
            self.err(output)


def _open_socket(command: WestCommand, remote_target: str) -> Optional[socket.socket]:
    """
    Attempts to connect to a socket.
    """
    try:
        host, port = remote_target.split(":")
        command.inf(f"Connecting to remote socket {host}:{port}...")

        port = int(port)
        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.connect((host, port))

        command.inf("Connected to remote socket successfully.")
        return remote_socket

    except Exception as e:
        command.die(f"Failed to connect to remote socket {e}")
