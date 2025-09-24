# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Zephelin West extension for tracing data capture."""

import signal
import subprocess
import time
from pathlib import Path
from textwrap import dedent

import serial
import usb.core
import usb.util
from tqdm import tqdm
from west.commands import WestCommand

CTF_TRACE_START_TAG = b"_zpl_ctf_start__"


class ZplGdbCapture(WestCommand):
    """Main class for the zpl-gdb-capture command."""

    def __init__(self):
        """Init function for the zpl-gdb-capture command."""
        super().__init__(
            "zpl-gdb-capture",
            "Capture traces using GDB",
            dedent("""
                Capture traces using GDB.

                This command captures traces using GDB from RAM using the `dump` command."""),
        )

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name, help=self.help, description=self.description)

        parser.add_argument("elf_path", help="Zephyr ELF path")
        parser.add_argument("output_path", help="Capture output path")
        parser.add_argument(
            "--no-debug-server", help="Don't set up the debug server", action="store_true"
        )
        parser.add_argument("--gdb-port", help="GDB server port", type=int, default=3333)

        return parser

    def do_run(self, args, unknown_args):
        self.inf(f"Capturing traces to {args.output_path}...")

        if args.gdb_port not in range(65536):
            self.die(f"The GDB port ({args.gdb_port}) is invalid. Should be a 0-65535 value.")

        if not args.no_debug_server:
            self.inf(f"Setting up the debug server on port {args.gdb_port}...")
            cmd_debugserver = f"west debugserver --gdb-port {args.gdb_port}".split()
            proc_debugserver = subprocess.Popen(
                cmd_debugserver, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

        self.inf("Waiting for the debugserver to start...")
        time.sleep(2)

        cmd_gdb = [
            "gdb-multiarch",
            "-batch",
            "-ex",
            "set pagination off",
            "-ex",
            f"target remote :{args.gdb_port}",
            "-ex",
            "set $start = &ram_tracing",
            "-ex",
            "set $end = (char*)&ram_tracing + sizeof(ram_tracing)",
            "-ex",
            f"dump binary memory {args.output_path} $start $end",
            "-ex",
            "quit",
            args.elf_path,
        ]

        self.inf("Saving traces...")
        proc_gdb = subprocess.Popen(cmd_gdb, stdout=subprocess.PIPE)
        (output, _) = proc_gdb.communicate()
        exit_code = proc_gdb.wait()

        if exit_code != 0:
            self.err(output)
            self.die("Failed to capture tracing data!")

        if not args.no_debug_server:
            self.inf("Stopping the debugserver...")
            proc_debugserver.send_signal(signal.SIGINT)

        self.inf("Done.")


class ZplUartCapture(WestCommand):
    """Main class for the zpl-uart-capture command."""

    def __init__(self):
        """Init function for the zpl-uart-capture command."""
        super().__init__(
            "zpl-uart-capture",
            "Capture traces using UART",
            dedent("""
                Capture traces using UART.

                This command capures traces using the serial interface."""),
        )

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name, help=self.help, description=self.description)

        parser.add_argument("serial_port", help="Seral port")
        parser.add_argument("serial_baudrate", help="Seral baudrate")
        parser.add_argument("output_path", help="Capture output path", type=Path)
        parser.add_argument(
            "--send_enable",
            action="store_true",
            help=(
                "Send 'enable' to device before collecting data to enable tracing, requires "
                "CONFIG_TRACING_HANDLE_HOST_CMD to be enabled in the app"
            ),
        )

        return parser

    def do_run(self, args, unknown_args):
        ser = serial.Serial(args.serial_port, args.serial_baudrate)
        if ser.is_open:
            self.inf(f"Capturing traces on {ser.port}@{ser.baudrate}...")
            self.inf("Press C-c to stop.")
        else:
            self.die(f"Couldn't open port {ser.port}!")

        trace_idx = 0
        buff = b""
        progress_bar = tqdm(unit="B", unit_scale=True)
        f = open(args.output_path, "wb")

        tqdm.write(f"Writing trace to {args.output_path}")

        if args.send_enable:
            ser.write(b"enable\r\n")
            tqdm.write("Sent b'enable'")

        try:
            while True:
                data = ser.read_all()
                progress_bar.update(len(data))

                if args.send_enable:
                    f.write(data)
                    continue

                buff += data

                if CTF_TRACE_START_TAG in buff:
                    tag_idx = buff.index(CTF_TRACE_START_TAG)
                    f.write(buff[:tag_idx])
                    f.close()
                    output_path = args.output_path.with_stem(
                        args.output_path.stem + f"_{trace_idx}"
                    )
                    tqdm.write(f"Found CTF trace start, writing trace to new file {output_path}")
                    f = open(output_path, "wb")
                    buff = buff[tag_idx + len(CTF_TRACE_START_TAG) :]
                    progress_bar.reset()
                    progress_bar.update(len(buff))
                    trace_idx += 1

                elif len(buff) > len(CTF_TRACE_START_TAG):
                    f.write(buff[: -len(CTF_TRACE_START_TAG)])
                    buff = buff[-len(CTF_TRACE_START_TAG) :]

        except KeyboardInterrupt:
            f.write(buff)
        finally:
            f.close()
            ser.close()
            progress_bar.close()


class ZplUsbCapture(WestCommand):
    """Main class for the zpl-usb-capture command."""

    def __init__(self):
        """Init function for the zpl-usb-capture command."""
        super().__init__(
            "zpl-usb-capture",
            "Capture traces using usb",
            dedent("""
                Capture traces using USB.

                This command capures traces using USB."""),
        )

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name, help=self.help, description=self.description)

        parser.add_argument("vendor_id", help="Vendor ID")
        parser.add_argument("product_id", help="Product ID")
        parser.add_argument("output_path", help="Capture output path")
        parser.add_argument(
            "-t", "--timeout", help="Timeout of the USB capture in seconds", type=int, default=2
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

        with open(args.output_path, "wb") as f:
            while True:
                try:
                    buf = usb.util.create_buffer(10 * 1024)
                    read_ep.read(buf, args.timeout * 1000)
                    f.write("".join([chr(x) for x in buf]).encode())
                except usb.core.USBTimeoutError:
                    self.die("USB operation timeout!")
                except KeyboardInterrupt:
                    break


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

        parser.add_argument("elf_path", help="Zephyr ELF path")
        parser.add_argument("config", help="Config to set")
        parser.add_argument("value", help="Value of the config (enable/disable)")

        return parser

    def do_run(self, args, unknown_args):
        self.inf(f"Setting {args.config} config to {args.value}")

        cmd = [
            "gdb-multiarch",
            "-batch",
            "-ex",
            "set pagination off",
            "-ex",
            "target remote :3333",
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
