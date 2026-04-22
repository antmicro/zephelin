# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides a handler for trace collection related tasks.
"""

from handlers.base import BaseHandler
import asyncio
from pathlib import Path

from config import TraceConfig
from socketio import AsyncServer
from state_manager import global_state

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ctf2tef import ctf_to_tef, prepare_dir  # noqa: E402
from prepare_trace import (  # noqa: E402
    CUSTOM_METADATA,
    create_custom_events,
)

PARSE_THRESHOLD_BYTES = 8192



class TraceHandler(BaseHandler):
    """
    Handler responsible for managing the lifecycle of trace data collection.
    """

    def __init__(
        self,
        sio: AsyncServer,
        traceConfig: TraceConfig,
    ):
        """
        Builds the TraceHandler.

        Parameters
        ----------
        sio: AsyncServer
            Instance of socketio asynchronous server.
        traceConfig: TraceConfig
            Configuration for trace gathering.
        """
        self.sio = sio
        self.tcp_host = traceConfig.tcp_host
        self.tcp_port = traceConfig.tcp_port

        self.raw_ctf_path = Path("live_capture.ctf")
        self.events_sent_count = 0
        self.unprocessed_bytes = 0
        self.file_handle = None

        self.trace_socket: Optional[asyncio.Server] = None
        self.active_writer: Optional[asyncio.StreamWriter] = None

        self.sync_tag = b"_zpl_ctf_start__"
        self.is_synced = False
        self.sync_buffer = bytearray()
        self.trace_threads = {}

        # Prevents 2 threads from reading CTF file at the same time
        self._is_parsing = False

        self.continuous_streaming = False

    async def connect(self) -> dict[str, str]:
        """
        Starts the TCP server to listen for incoming trace streams from capture scripts.

        Raises
        ------
        Exception
            If the server is already listening or a trace is active.
        """
        print("[TRACE HANDLER] Connection initializing")
        if global_state.trace_active or self.trace_socket:
            raise Exception("Already listening for traces.")

        self.trace_socket = await asyncio.start_server(
            self._handle_client, self.tcp_host, self.tcp_port
        )
        global_state.trace_active = True

        print(f"[TRACE HANDLER] Listening for trace streams on {self.tcp_host}:{self.tcp_port}")
        return {
            "status": "success",
            "message": f"Listening for traces on {self.tcp_host}:{self.tcp_port}",
        }

    async def disconnect(self) -> dict[str, str]:
        """
        Terminates the background read task and tears down transportation backend.

        Returns
        -------
            Message with connection status.
        """
        print("[TRACE HANDLER] Disconnecting")

        global_state.trace_active = False

        if self.trace_socket:
            self.trace_socket.close()
            await self.trace_socket.wait_closed()
            self.trace_socket = None

        if self.active_writer:
            self.active_writer.close()
            await self.active_writer.wait_closed()
            self.active_writer = None

        if not global_state.trace_active:
            return {"status": "success", "message": "Trace was already stopped."}

        if global_state.read_task:
            global_state.read_task.cancel()
            global_state.read_task = None

        return {"status": "success", "message": "Trace stopping initiated."}

    async def stream_start(self) -> dict[str, str]:
        """Enables continuous trace streaming to the frontend."""
        self.continuous_streaming = True
        return {"status": "success"}

    async def stream_stop(self) -> dict[str, str]:
        """Disables continuous trace streaming to the frontend."""
        self.continuous_streaming = False
        return {"status": "success"}

    async def metadata(self):
        """
        Provides model metadata and memory symbols for the trace.
        """
        raise NotImplementedError

    async def reset(self):
        """Resets the trace buffer."""
        raise NotImplementedError

    async def collect(self) -> dict:
        """Provides the increment of the trace buffer not yet sent."""
        print("[TRACE HANDLER] Collecting trace increment")

        if not self.raw_ctf_path.exists():
            return {"status": "error", "message": "No trace data available to collect."}

        if self.file_handle and not self.file_handle.closed:
            self.file_handle.flush()

        self._is_parsing = True

        try:
            payload_events, overlap_count, _ = await self._extract_trace_increment(
                update_state=True
            )

            return {
                "status": "success",
                "data": {
                    "events": payload_events,
                    "overlap_count": overlap_count,
                    "total_count": self.events_sent_count,
                },
            }

        except Exception as e:
            print(f"[Trace Handler] Full collection parse error: {e}")
            return {"status": "error", "message": f"Failed to parse trace file: {e}"}
        finally:
            self._is_parsing = False

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Callback triggered when a remote capture script connects to the socket.
        """
        peer_name = writer.get_extra_info("peername")
        print(f"[TRACE HANDLER] Client connected from {peer_name}")

        # Prevent multiple capture scripts from streaming at the exact same time
        if self.active_writer is not None:
            print("[TRACE HANDLER] Rejecting new connection, already streaming.")
            writer.close()
            await writer.wait_closed()
            return

        self.active_writer = writer

        self.raw_ctf_path.parent.mkdir(exist_ok=True)
        self.file_handle = open(self.raw_ctf_path, "wb")
        self.events_sent_count = 0
        self.is_synced = False
        self.sync_buffer.clear()
        self.trace_threads.clear()

        global_state.read_task = asyncio.current_task()

        try:
            while global_state.trace_active:
                chunk = await reader.read(PARSE_THRESHOLD_BYTES)

                if not chunk:
                    print("[TRACE HANDLER] Client disconnected, EOF reached.")
                    break

                await self._handle_trace(chunk)

        except asyncio.CancelledError:
            print("\n[TRACE HANDLER] Reading loop cancelled.")
        except Exception as e:
            print(f"\n[TRACE HANDLER] Error reading from socket: {e}")
        finally:
            if self.file_handle:
                self.file_handle.close()
                self.file_handle = None

            if self.is_synced:
                await self._safe_parse_and_emmit()

            writer.close()
            await writer.wait_closed()
            self.active_writer = None
            print("[TRACE HANDLER] Client connection cleaned up.")

    async def _handle_trace(self, trace_chunk: bytes):
        """
        Handles the received chunk by converting it to TEF and emitting it further.

        Parameters
        ----------
        trace_chunk: bytes
            Raw trace in CTF format.
        """
        if not self.file_handle:
            return

        self.sync_buffer.extend(trace_chunk)

        tag_idx = self.sync_buffer.find(self.sync_tag)

        if tag_idx != -1:
            if not self.is_synced:
                print("\n [Trace Handler] Found START TAG Valid CTF data starting")
                self.is_synced = True
            valid_data = self.sync_buffer[tag_idx + len(self.sync_tag) :]

            self.sync_buffer.clear()
            self.sync_buffer.extend(valid_data)

        if self.is_synced:
            if len(self.sync_buffer) > len(self.sync_tag):
                safe_to_write = self.sync_buffer[: -len(self.sync_tag)]

                self.file_handle.write(safe_to_write)
                self.file_handle.flush()
                self.unprocessed_bytes += len(safe_to_write)

                self.sync_buffer = self.sync_buffer[-len(self.sync_tag) :]

            # Only one parsing thread can be spawned because of the limitation that bt2
            # must parse data from byte 0 each time. This lock prevents multiple
            # threads reading the same file. Also prevents race conditions from
            # corrupting 'events_sent_count'.
            if self.unprocessed_bytes >= PARSE_THRESHOLD_BYTES and not self._is_parsing:
                self._is_parsing = True
                self.unprocessed_bytes = 0
                asyncio.create_task(self._safe_parse_and_emmit())
        else:
            # Keep enough bytes in memory to not miss the start tag
            sliding_window_bytes = 50
            if len(self.sync_buffer) > sliding_window_bytes:
                self.sync_buffer = self.sync_buffer[-sliding_window_bytes:]

    async def _safe_parse_and_emmit(self):
        """
        Makes sure the parsing lock is always cleared even if _parse_and_emit_diff crashes.
        """
        try:
            await self._parse_and_emit_diff()
        finally:
            self._is_parsing = False

    def _get_sliding_window(
        self, trace_events: list, window_size: int = 150
    ) -> tuple[list, int, int]:
        """
        Applies a sliding window to the trace events to recover late-arriving packets
        that Babeltrace inserts into the recent past.

        Parameters
        ----------
        trace_events: list
            List of all gathered events.
        window_size: int
            Determines how many safety events should be sent.

        Returns
        -------
        tuple[list, int, int]
            Safety events, how big is the overlap, total count of events.
        """
        total_events = len(trace_events)

        if total_events <= self.events_sent_count:
            return [], 0, self.events_sent_count

        slice_start = max(0, self.events_sent_count - window_size)

        overlap_count = min(self.events_sent_count, window_size)

        windowed_events = trace_events[slice_start:]

        return windowed_events, overlap_count, total_events

    async def _extract_trace_increment(self, update_state: bool) -> tuple[list, int, int]:
        """
        Parses the CTF file, calculates the sliding window, and formats thread metadata.
        If update_state is True, it commits the changes to the internal tracking variables.
        """

        def run_sync_parse():
            with prepare_dir(self.raw_ctf_path) as tmp_dir:
                result = ctf_to_tef(
                    path=str(tmp_dir),
                    custom_metadata=CUSTOM_METADATA,
                    custom_events=create_custom_events(),
                )
            return result.tef, result.thread_names

        loop = asyncio.get_event_loop()
        trace_events, thread_names = await loop.run_in_executor(None, run_sync_parse)

        windowed_events, overlap_count, new_total_count = self._get_sliding_window(
            trace_events, window_size=150
        )

        payload_events = []

        if new_total_count > self.events_sent_count:
            if update_state:
                self.events_sent_count = new_total_count

                new_metadata = []
                for t_name, tid in thread_names.items():
                    if self.trace_threads.get(tid) != t_name:
                        new_metadata.append({
                            "name": "thread_name",
                            "cat": "zephyr",
                            "ph": "M",
                            "pid": 0,
                            "tid": tid,
                            "args": {"name": t_name},
                        })
                        self.trace_threads[tid] = t_name

                payload_events = new_metadata + windowed_events

        return payload_events, overlap_count, new_total_count

    async def _parse_and_emit_diff(self):
        """
        Converts CTF data in the buffer file into TEF and emits events that were not previously
        emitted.
        """
        try:
            previous_count = self.events_sent_count

            payload_events, overlap_count, new_total_count = await self._extract_trace_increment(
                update_state=self.continuous_streaming
            )

            if new_total_count > previous_count:
                if self.continuous_streaming:
                    await self.sio.emit(
                        "rpc_notification",
                        {
                            "jsonrpc": "2.0",
                            "method": "trace.events",
                            "params": {
                                "events": payload_events,
                                "overlap_count": overlap_count,
                                "total_count": self.events_sent_count,
                            },
                        },
                    )
                else:
                    await self.sio.emit(
                        "rpc_notification",
                        {
                            "jsonrpc": "2.0",
                            "method": "trace.status",
                            "params": {
                                "total_count": new_total_count,
                            },
                        },
                    )
        except Exception as e:
            # It is expected that some parsed events will be incomplete
            if "LTTNG_CTF_LTTNG_INDEX" not in str(e):
                print(f"[Trace Handler] Incremental parse error: {e}")
