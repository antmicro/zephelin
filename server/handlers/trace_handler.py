# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides a handler for trace collection related tasks.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Union

from config import TraceConfig
from ctf2tef import ctf_to_tef, prepare_dir
from extract_tvm_model_data import tvm_recalculate_model_numbers
from handlers.base import BaseHandler
from prepare_trace import (
    CUSTOM_METADATA,
    MODEL_IDS_MAPPING,
    REGION_SIZES,
    add_model_metadata,
    create_custom_events,
    extract_memory_symbols,
    extract_symbol_map,
    process_ram_report,
)
from socketio import AsyncServer
from state_manager import global_state

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PARSE_THRESHOLD_BYTES = 8192

logger = logging.getLogger("TraceHandler")


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

        self.build_dir = traceConfig.build_dir
        self.tflm_model_paths = traceConfig.tflm_model_paths
        self.tvm_model_paths = traceConfig.tvm_model_paths
        self.tvm_model_metadata_paths = traceConfig.tvm_model_metadata_paths

        self.tvm_op_remove_prefix = traceConfig.tvm_model_op_remove_prefix
        self.tvm_op_remove_suffix = traceConfig.tvm_model_op_remove_suffix

        tflm_model_count = len(self.tflm_model_paths or [])
        tvm_model_count = len(self.tvm_model_paths or [])
        self.multi_model_trace = tflm_model_count + tvm_model_count >= 2

        self.symbol_map = {}
        self.tvm_prefix_to_model_id = {}

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

        Returns
        -------
        dict[str, str]
            Status message.

        Raises
        ------
        Exception
            If the server is already listening or a trace is active.
        """
        logger.info("Connection initializing")
        if global_state.trace_active or self.trace_socket:
            raise Exception("Already listening for traces.")

        self.trace_socket = await asyncio.start_server(
            self._handle_client, self.tcp_host, self.tcp_port
        )
        global_state.trace_active = True

        logger.info(f" Listening for trace streams on {self.tcp_host}:{self.tcp_port}")
        return {
            "status": "success",
            "message": f"Listening for traces on {self.tcp_host}:{self.tcp_port}",
        }

    async def disconnect(self) -> dict[str, str]:
        """
        Terminates the background read task and tears down transportation backend.

        Returns
        -------
        dict[str, str]
            Status message.
        """
        logger.info("Disconnecting")

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
            logger.debug("Trace was already stopped.")
            return {"status": "success", "message": "Trace was already stopped."}

        if global_state.read_task:
            global_state.read_task.cancel()
            global_state.read_task = None

        return {"status": "success", "message": "Trace stopping initiated."}

    async def stream_start(self) -> dict[str, str]:
        """
        Enables continuous trace streaming to the frontend.

        Returns
        -------
        dict[str, str]
            Status message.
        """
        self.continuous_streaming = True
        logger.debug("Continous streaming enabled.")
        return {"status": "success"}

    async def stream_stop(self) -> dict[str, str]:
        """
        Disables continuous trace streaming to the frontend.

        Returns
        -------
        dict[str, str]
            Status message.
        """
        self.continuous_streaming = False
        logger.debug("Continous streaming disabled.")
        return {"status": "success"}

    async def metadata(self) -> dict[str, Union[str, dict]]:
        """
        Provides model metadata and memory symbols for the trace.

        Returns
        -------
        dict[str, Union[str, dict]]
            Message with metadata events or error.
        """
        logger.info("Collecting trace metadata")

        try:
            tef_metadata_events = []
            zephyr_elf_path = self.build_dir / "zephyr" / "zephyr.elf"

            if zephyr_elf_path.exists():
                self.symbol_map = extract_symbol_map(zephyr_elf_path)

                if REGION_SIZES:
                    mem_symbols = extract_memory_symbols(self.symbol_map)
                    tef_metadata_events.append({
                        "name": "MEMORY::SYMBOLS",
                        "cat": "zephyr",
                        "ph": "M",
                        "pid": 0,
                        "tid": 0,
                        "ts": 0,
                        "args": mem_symbols,
                    })

                ram_report = self.build_dir / "ram.json"
                if ram_report.exists():
                    with ram_report.open("r") as fd:
                        ram = json.load(fd).get("symbols", {})

                    if ram:
                        process_ram_report(ram)
                        tef_metadata_events.append({
                            "name": "MEMORY::STATICALLY_ASSIGNED_MEM",
                            "cat": "zephyr",
                            "ph": "M",
                            "pid": 0,
                            "tid": 0,
                            "ts": 0,
                            "args": ram.get("size", 0),
                        })
            else:
                logger.warning(f" Zephyr ELF not found at {zephyr_elf_path}.")

            if self.tflm_model_paths:
                logger.debug("Adding TFLM model metadata.")
                from extract_tflite_model_data import extract_model_data

                for tflm_model_path in self.tflm_model_paths:
                    if tflm_model_path.exists():
                        metadata = extract_model_data(
                            tflm_model_path, PROJECT_ROOT, zephyr_elf_path, None
                        )
                        if "id" not in metadata:
                            add_model_metadata(tef_metadata_events, metadata)
                        else:
                            for model_id in metadata["id"]:
                                add_model_metadata(tef_metadata_events, metadata | {"id": model_id})

            if self.tvm_model_paths:
                logger.debug("Adding TVM model metadata.")
                from extract_tvm_model_data import extract_models_data

                for metadata in extract_models_data(
                    self.tvm_model_paths,
                    self.tvm_model_metadata_paths,
                    model_op_remove_prefix=self.tvm_op_remove_prefix,
                    model_op_remove_suffix=self.tvm_op_remove_suffix,
                    prefix_to_model_id=self.tvm_prefix_to_model_id,
                ):
                    add_model_metadata(tef_metadata_events, metadata)

            return {"status": "success", "data": {"events": tef_metadata_events}}

        except Exception as e:
            logger.error(f"Metadata collection error: {e}")
            return {"status": "error", "message": f"Failed to collect metadata: {e}"}

    async def reset(self):
        """Resets the trace buffer."""
        raise NotImplementedError

    async def collect(self) -> dict[str, Union[str, dict]]:
        """
        Provides the increment of the trace buffer not yet sent.

        Returns
        -------
        dict[str, Union[str, dict]]
            Message with all events present in the buffer or error.
        """
        logger.info("Collecting trace increment")

        if not self.raw_ctf_path.exists():
            logger.warning("No trace data available to collect.")
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
            logger.error(f" Trace collection parse error: {e}")
            return {"status": "error", "message": f"Failed to parse trace file: {e}"}
        finally:
            self._is_parsing = False

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Callback triggered when a remote capture script connects to the socket.

        Parameters
        ----------
        reader: asyncio.StreamReader
            Instance of stream reader.

        writer: asyncio.StreamWriter
            Instance of stream writer.
        """
        peer_name = writer.get_extra_info("peername")
        logger.info(f"Client connected from {peer_name}")

        # Prevent multiple capture scripts from streaming at the exact same time
        if self.active_writer is not None:
            logger.warning("Rejecting new connection, already streaming.")
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
                    logger.info("Client disconnected, EOF reached.")
                    break

                await self._handle_trace(chunk)

        except asyncio.CancelledError:
            logger.info("Reading loop cancelled.")
        except Exception as e:
            logger.error(f"Error reading from socket: {e}")
        finally:
            if self.file_handle:
                self.file_handle.close()
                self.file_handle = None

            if self.is_synced:
                await self._safe_parse_and_emmit()

            writer.close()
            await writer.wait_closed()
            self.active_writer = None
            logger.info("Client connection cleaned up.")

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
                logger.debug("Found START TAG Valid CTF data starting")
                self.is_synced = True

            self.sync_buffer = self.sync_buffer[tag_idx + len(self.sync_tag) :]

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

        Parameters
        ----------
        update_state: bool
            Serves as commit flag, if false only total_count is emitted.

        Returns
        -------
        tuple[list, int, int]
            TEF events, how big is the overlap, total count of events.
        """

        def run_sync_parse():
            MODEL_IDS_MAPPING.clear()
            self.tvm_prefix_to_model_id.clear()

            with prepare_dir(self.raw_ctf_path) as tmp_dir:
                result = ctf_to_tef(
                    path=str(tmp_dir),
                    custom_metadata=CUSTOM_METADATA,
                    custom_events=create_custom_events(
                        tvm_op_remove_prefix=self.tvm_op_remove_prefix,
                        tvm_op_remove_suffix=self.tvm_op_remove_suffix,
                        multi_model_trace=self.multi_model_trace,
                        symbol_map=self.symbol_map,
                    ),
                )

            trace_events = result.tef

            if self.tvm_model_paths:
                if 0 in MODEL_IDS_MAPPING:
                    MODEL_IDS_MAPPING.pop(0)

                trace_events, tvm_prefix_to_model_id = tvm_recalculate_model_numbers(
                    trace_events, len(MODEL_IDS_MAPPING)
                )

                MODEL_IDS_MAPPING.update(tvm_prefix_to_model_id)
                self.tvm_prefix_to_model_id.update(tvm_prefix_to_model_id)

            return trace_events, result.thread_names

        loop = asyncio.get_event_loop()
        trace_events, thread_names = await loop.run_in_executor(None, run_sync_parse)

        windowed_events, overlap_count, new_total_count = self._get_sliding_window(
            trace_events, window_size=150
        )

        payload_events = []

        if (new_total_count > self.events_sent_count) and update_state:
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
                logger.error(f"Incremental parse error: {e}")
