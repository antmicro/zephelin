"""
Provides Robot Framework keywords that use Babeltrace2 to validate traces.
"""

import collections.abc
import math
import numbers
import os
import shutil
import tempfile
import time
from pathlib import Path
from socket import socket
from typing import Any

import bt2

_DEFAULT_TIMEOUT = 10.0


class UnexpectedTraceFoundError(Exception):
    """
    Raised when unexpected trace is found in CTF stream.
    """


class TraceTester:
    """
    Provides methods for testing whether trace events are present in CTF stream.
    """

    def __init__(self):
        """
        Creates TraceTester.
        """
        self.sock = None
        self.ctf_dir = Path(tempfile.mkdtemp())

        # prepare directory with traces and metadata for babeltrace
        metadata_zephyr_path = Path(os.environ["ZEPHYR_BASE"]) / "subsys/tracing/ctf/tsdl/metadata"
        metadata_zpl_path = Path(__file__).parent.parent / "zpl/metadata"

        metadata_zephyr = metadata_zephyr_path.read_text()
        metadata_zpl = metadata_zpl_path.read_text()

        metadata_path = self.ctf_dir / "metadata"
        self.ctf_path = self.ctf_dir / "channel0"

        # merge Zephyr and ZPL metadata
        metadata_path.write_text(f"{metadata_zephyr}\n{metadata_zpl}")

    def __del__(self):
        shutil.rmtree(self.ctf_dir)

    def trace_tester_open_socket(self, uart_socket_port: int):
        """
        Opens server socket created by Renode that will be used for reading CTF stream.

        Parameters
        ----------
        uart_socket_port : int
            Port of the server socket.
        """
        self.sock = socket()
        self.sock.settimeout(0.001)  # 1ms
        self.sock.connect(("localhost", uart_socket_port))

    def trace_tester_close_socket(self):
        """
        Closes server socket.
        """
        if self.sock is None:
            return

        self.sock.close()
        self.sock = None

    def wait_for_trace_on_uart(
        self,
        trace_name: str,
        timeout: float = _DEFAULT_TIMEOUT,
        **trace_fields: Any,
    ):
        """
        Reads CTF stream until provided trace is found. If the timeout is hit, raises exception.

        Parameters
        ----------
        trace_name : str
            Name of the trace.
        timeout : float
            Timeout in seconds.
        trace_fields : Any
            Payload fields of the trace.

        Raises
        ------
        TimeoutError
            Raised when provided trace is not found.
        """
        self.__read_traces_until_trace(trace_name, timeout, **trace_fields)

    def trace_should_not_be_on_uart(
        self,
        trace_name: str,
        timeout: float = _DEFAULT_TIMEOUT,
        **trace_fields,
    ):
        """
        Reads CTF stream until provided trace is found. If it is found raises
        UnexpectedTraceFoundError.

        Parameters
        ----------
        trace_name : str
            Name of the trace.
        timeout : float
            Timeout in seconds.
        trace_fields : Any
            Payload fields of the trace.

        Raises
        ------
        UnexpectedTraceFoundError
            Raised when provided trace is found.
        """
        try:
            self.__read_traces_until_trace(trace_name, timeout, **trace_fields)
        except TimeoutError:
            pass
        else:
            raise UnexpectedTraceFoundError(f"Unexpected trace read {trace_name} {trace_fields}")

    def __read_traces_until_trace(
        self,
        trace_name: str,
        timeout: float = _DEFAULT_TIMEOUT,
        **trace_fields,
    ):
        start = time.perf_counter()
        ctf_stream = b""
        traces_str = ""
        trace_found = False

        while True:
            if time.perf_counter() - start > timeout:
                raise TimeoutError(
                    f"Trace {trace_name} {trace_fields} not found.\nParsed traces:\n{traces_str}"
                )

            try:
                # read stream byte by byte so that no extra bytes are read
                ctf_stream += self.sock.recv(1)
            except TimeoutError:
                # no new data
                continue

            self.ctf_path.write_bytes(ctf_stream)

            try:
                # parse traces
                traces = list(bt2.TraceCollectionMessageIterator(str(self.ctf_dir)))

                for trace in traces:
                    # check if trace type is proper
                    if not isinstance(trace, bt2._EventMessageConst):
                        continue

                    traces_str += (
                        f"\t{trace.default_clock_snapshot.ns_from_origin / 1e9} s"
                        f" {trace.event.name} {trace.event.payload_field}\n"
                    )

                    # check trace event name
                    if trace.event.name != trace_name:
                        continue

                    # check whether trace event fields match
                    if self.__event_fields_is_subset(trace_fields, trace.event.payload_field):
                        trace_found = True
                        break

                if trace_found:
                    # break main loop
                    break

            except bt2._Error:
                # traces could not be parsed
                pass

            else:
                # clear CTF stream so that it does not parse the same traces multiple times
                ctf_stream = b""

    @staticmethod
    def __event_fields_is_subset(
        fields_a: dict,
        fields_b: bt2._StructureFieldConst,
    ) -> bool:
        for field_name, field_value in fields_a.items():
            if field_name not in fields_b:
                # field not present in second event
                return False

            if field_value == "any":
                # check only whether the field is present
                continue

            if isinstance(field_value, list):
                # compare iterables
                if not isinstance(fields_b[field_name], collections.abc.Sequence):
                    return False
                if len(fields_b[field_name]) != len(field_value):
                    return False
                if any(
                    (x != y and not (math.isnan(x) and math.isnan(y)))
                    for x, y in zip(fields_b[field_name], field_value)
                ):
                    return False

            elif isinstance(fields_b[field_name], numbers.Integral):
                # compare integers (includes enums)
                if int(fields_b[field_name]) != field_value:
                    return False

            elif fields_b[field_name] != field_value:
                # generic comparison
                return False

        return True
