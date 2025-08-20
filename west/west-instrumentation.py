"""ZPL West extension for instrumentation data capture."""

from textwrap import dedent

import serial
from west.commands import WestCommand


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
    """Main class for the instrumentation-uart-capture command."""

    def __init__(self):
        """Init function for the instrumentation-uart-capture command."""
        super().__init__(
            "instrumentation-uart-capture",
            "Capture instrumentation traces using UART",
            dedent("""
                Capture instrumentation traces using UART.

                This command capures traces using the serial interface."""),
        )

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name, help=self.help, description=self.description)

        parser.add_argument("serial_port", help="Seral port")
        parser.add_argument("serial_baudrate", help="Seral baudrate")
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
            f.write(stream)

        ser.close()
