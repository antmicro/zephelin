# Copyright (c) 2025-2026 Analog Devices, Inc.
# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

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

_TRACE_PRESENT_TIMEOUT = 100.0
_TRACE_ABSENT_TIMEOUT = 10.0
_PARSING_THROTTLE_TIME = 0.5

_CTF_TRACE_START_TAG = b"_zpl_ctf_start__"


class UnexpectedTraceFoundError(Exception):
    """
    Raised when unexpected trace is found in CTF stream.
    """


class InvalidTrace(Exception):
    """
    Raised when provided trace is invalid.
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

        self._ctf_stream = bytearray()

        self._parsed_traces = []
        self._processed_trace_count = 0

        # prepare directory with traces and metadata for babeltrace
        metadata_zephyr_path = Path(os.environ["ZEPHYR_BASE"]) / "subsys/tracing/ctf/tsdl/metadata"
        metadata_zpl_path = Path(__file__).parent.parent.parent / "zpl/metadata"

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
        timeout: float = _TRACE_PRESENT_TIMEOUT,
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
        timeout: float = _TRACE_ABSENT_TIMEOUT,
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
        timeout: float = _TRACE_PRESENT_TIMEOUT,
        **trace_fields,
    ):
        start = time.perf_counter()
        last_parse_time = 0.0
        trace_found = False

        with open(self.ctf_path, "wb") as ctf_file:
            while True:
                # global timeout
                if time.perf_counter() - start > timeout:
                    error_log = "\n".join(
                        f"\t{t['timestamp'] / 1e9} s {t['name']} {t['payload']}"
                        for t in self._parsed_traces
                    )
                    raise TimeoutError(
                        f"Trace {trace_name} {trace_fields} not found.\nParsed traces:\n{error_log}"
                    )

                # drain socket 4096 bytes at a time
                try:
                    chunk = self.sock.recv(4096)
                    if chunk:
                        self._ctf_stream.extend(chunk)
                    else:
                        raise ConnectionError(
                            f"Emulator closed the socked before {trace_name} could be found."
                        )
                except TimeoutError:
                    pass

                if self._ctf_stream:
                    tag_idx = self._ctf_stream.rfind(_CTF_TRACE_START_TAG)
                    # start recording a trace
                    if tag_idx != -1:
                        self._ctf_stream = self._ctf_stream[tag_idx + len(_CTF_TRACE_START_TAG) :]
                        self._parsed_traces.clear()
                        self._processed_trace_count = 0

                # call bt2 periodically to prevent it from choking on short byte sequences
                if self._ctf_stream:
                    current_time = time.perf_counter()
                    if current_time - last_parse_time >= _PARSING_THROTTLE_TIME:
                        last_parse_time = current_time

                        # write bytes to the file
                        ctf_file.seek(0)
                        ctf_file.truncate()
                        ctf_file.write(self._ctf_stream)
                        ctf_file.flush()

                        extracted_traces = []
                        try:
                            for msg in bt2.TraceCollectionMessageIterator(str(self.ctf_dir)):
                                if isinstance(msg, bt2._EventMessageConst):
                                    timestamp = msg.default_clock_snapshot.ns_from_origin
                                    payload = dict(msg.event.payload_field)
                                    payload["timestamp"] = timestamp

                                    # convert C-pointer from bt2 into native Python dicts
                                    extracted_traces.append({
                                        "name": msg.event.name,
                                        "timestamp": timestamp,
                                        "payload": payload,
                                    })
                        except bt2._Error:
                            # if file contains partial traces, ignore and try to parse
                            # them on the next iteration
                            pass
                        else:
                            self._parsed_traces = extracted_traces

                # only check traces that arrived after current bookmark
                new_traces = self._parsed_traces[self._processed_trace_count :]

                for i, trace in enumerate(new_traces):
                    if trace["name"] != trace_name:
                        continue

                    if trace["timestamp"] <= 0:
                        raise InvalidTrace("Timestamp must be positive")

                    if self.__event_fields_is_subset(trace_fields, trace["payload"]):
                        trace_found = True
                        self._processed_trace_count += i + 1
                        break

                if trace_found:
                    # break main loop
                    break

    @staticmethod
    def __event_fields_is_subset(
        fields_a: dict,
        fields_b: dict,
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
