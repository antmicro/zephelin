# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Zeppelin West extension for tracing data capture."""

import signal
import subprocess
import time
from textwrap import dedent

import serial
import usb.core
import usb.util
from west.commands import WestCommand


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

        return parser

    def do_run(self, args, unknown_args):
        self.inf(f"Capturing traces to {args.output_path}...")

        cmd_debugserver = "west debugserver".split()
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
            "target remote :3333",
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
        parser.add_argument("output_path", help="Capture output path")

        return parser

    def do_run(self, args, unknown_args):
        ser = serial.Serial(args.serial_port, args.serial_baudrate)
        if ser.is_open:
            self.inf(f"Capturing traces on {ser.port}@{ser.baudrate}...")
            self.inf("Press C-c to stop.")
        else:
            self.die(f"Couldn't open port {ser.port}!")

        ser.write("enable\r".encode())

        with open(args.output_path, "wb") as f:
            while True:
                try:
                    while ser.inWaiting() > 0:
                        f.write(ser.read())
                except KeyboardInterrupt:
                    break

        ser.close()


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
