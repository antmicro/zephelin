# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides a handler for trace collection related tasks.
"""

import asyncio
import collections
import gc
import json
import logging
import struct
import tempfile
import time
from pathlib import Path
from threading import Lock, Thread
from typing import Literal, Union

import bt2
import server_utils.network as networking_utils
from config import TraceConfig
from ctf2tef import StreamingCTFToTEF, merge_metadata, stream_ctf_to_tef
from endpoints import Endpoints
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

BT2_BATCH_SIZE = 50
ZEPHYR_BASE = Path(__file__).resolve().parent.parent.parent.with_name("zephyr")
DATA_CHUNK_BYTES = 8192
_CTF_TRACE_START_TAG = b"_zpl_ctf_start__"

logger = logging.getLogger("TraceHandler")


class StreamParserProxy:
    """
    Class for intercepting and parsing the CTF data stream before it touches libbtrace.
    """

    def __init__(self, size_is_bits=True):
        """
        Initializes the proxy responsible for stream processing.

        Parameters
        ----------
        size_is_bits: bool
            Indicates whether the packet size specified in the CTF header is measured in bits.
        """
        self.buffer = bytearray()
        self.expected_size = None
        self.size_is_bits = size_is_bits
        self.is_synced = False

    def process_data(self, data: bytes):
        self.buffer.extend(data)

        while True:
            tag_idx = self.buffer.find(_CTF_TRACE_START_TAG)

            if tag_idx != -1:
                del self.buffer[: tag_idx + len(_CTF_TRACE_START_TAG)]
                self.is_synced = True
                self.expected_size = None
                yield "RESET", None
                continue

            # Ignore data before sync tag is detected
            if not self.is_synced:
                keep_len = len(_CTF_TRACE_START_TAG)
                if len(self.buffer) > keep_len:
                    # Keep just enough bytes in case the tag is split across network reads
                    del self.buffer[:-keep_len]
                break

            # Read the header of a packet to determine its size
            if self.expected_size is None:
                if len(self.buffer) >= 4:
                    # The 3rd and 4th bytes hold the packet size
                    _, packet_size = struct.unpack("<HH", self.buffer[:4])
                    self.expected_size = (packet_size // 8) if self.size_is_bits else packet_size

                    # A valid packet must at least contain its own 4-byte header
                    if self.expected_size < 4:
                        logger.warning(
                            f"Corrupt packet header (size={self.expected_size}); resyncing."
                        )
                        self.buffer.clear()
                        self.expected_size = None
                        self.is_synced = False
                        break
                else:
                    break

            # Buffer data until the complete packet is collected than yield
            if self.expected_size is not None:
                if len(self.buffer) >= self.expected_size:
                    packet = bytes(self.buffer[: self.expected_size])
                    del self.buffer[: self.expected_size]
                    self.expected_size = None
                    yield "PACKET", packet
                    continue
                else:
                    break


class TraceHandler(BaseHandler):
    """
    Handler responsible for managing the lifecycle of trace data collection.
    """

    endpoints = Endpoints()

    def __init__(
        self,
        sio: AsyncServer,
        traceConfig: TraceConfig,
    ):
        """
        Builds the TraceHandler.

        Every public method becomes and endpoint.
        Place '_' before methods that are not meant to be called externally.

        Parameters
        ----------
        sio: AsyncServer
            Instance of socketio asynchronous server.
        traceConfig: TraceConfig
            Configuration for trace gathering.
        """
        self.sio = sio
        self.trace_events = []
        self.tcp_host = traceConfig.tcp_host
        self.tcp_port = traceConfig.tcp_port
        self.bt_port = traceConfig.bt_port

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

        self.pending_events = []
        self.pending_metadata = []
        self.trace_threads = {}
        self.continuous_streaming = False
        self.bt2_thread = None
        self.bt2_thread_stop = False
        self.trace_lock = Lock()
        self.msg_it = None
        self.async_q = None
        self.tef_task = None
        self.interceptor_server = None
        self.interceptor_task = None
        self.ctf_tef: StreamingCTFToTEF | None = None
        self.ctf_tef_task: asyncio.Task | None = None
        self._emit_queue: asyncio.Queue[dict] | None = None
        self._emit_task: asyncio.Task | None = None

        self._prepare_metadata()

    def _init_emit(self) -> None:
        """Initialize the background emit task and its queue."""
        if self._emit_queue is not None:
            return
        self._emit_queue = asyncio.Queue()
        self._emit_task = asyncio.create_task(self._emit_loop())

    def _prepare_metadata(self) -> None:
        """
        Write the merged CTF metadata into a fresh temporary directory.
        """
        self._metadata_tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        try:
            merge_metadata(Path(self._metadata_tmp.name))
        except FileNotFoundError as e:
            self._metadata_tmp.cleanup()
            self._metadata_tmp = None
            raise Exception(f"Failed to prepare CTF metadata: {e}")
        self.metadata_dir = self._metadata_tmp.name

    @endpoints.register_method("trace.connect")
    async def connect(self) -> dict[Literal["status", "message"], str]:
        """
        Starts the TCP server to listen for incoming trace streams from capture scripts.

        Returns
        -------
        dict[Literal["status", "message"], str]
            Status message.

        Raises
        ------
        Exception
            If the server is already listening or a trace is active.
        """
        logger.info("Connection initializing")

        if self.bt2_thread is not None:
            raise Exception("Already listening for traces.")

        self.async_loop = asyncio.get_event_loop()
        self.async_q = asyncio.Queue(0)

        # Worker thread function for receiving bt2 messages
        def do_stream():
            ctf_plugin = bt2.find_plugin("ctf")
            dummy_cc = ctf_plugin.source_component_classes["live"]
            while True:
                try:
                    self.msg_it = bt2.TraceCollectionMessageIterator(
                        bt2.ComponentSpec(
                            dummy_cc,
                            {
                                "port": self.bt_port,
                                "metadata-path": self.metadata_dir,
                            },
                        ),
                        live_mode=True,
                    )
                    break
                except bt2._AddressInUseSocketError:
                    new_port = networking_utils.find_free_port()
                    logger.warning(
                        f"Port {self.bt_port}, set as --bt-port, is busy."
                        f" Using port {new_port} instead."
                    )
                    self.bt_port = new_port

            # Batch messages before crossing the thread boundary to avoid
            # per-message asyncio.run_coroutine_threadsafe overhead.
            batch = []

            # Iterate the trace messages.
            while not self.bt2_thread_stop:
                try:
                    msg = next(self.msg_it)
                    batch.append(msg)

                    if len(batch) >= BT2_BATCH_SIZE:
                        asyncio.run_coroutine_threadsafe(
                            self.async_q.put(tuple(batch)), self.async_loop
                        ).result()
                        batch = []
                except bt2.TryAgain:
                    # Flush any accumulated batch on TryAgain to avoid losing messages.
                    if batch:
                        asyncio.run_coroutine_threadsafe(
                            self.async_q.put(tuple(batch)), self.async_loop
                        ).result()
                        batch = []
                    continue

            # Drain remaining batch on shutdown
            if batch:
                asyncio.run_coroutine_threadsafe(
                    self.async_q.put(tuple(batch)), self.async_loop
                ).result()

        self.bt2_thread = Thread(target=do_stream)
        self.bt2_thread.start()
        self._init_emit()
        self.tef_task = asyncio.create_task(self._parse_and_emit_diff())

        self.interceptor_server = await asyncio.start_server(
            self._raw_trace_interceptor, self.tcp_host, self.tcp_port
        )
        self.interceptor_task = asyncio.create_task(self.interceptor_server.serve_forever())

        return {
            "status": "success",
            "message": f"Interceptor proxy ready on port {self.tcp_port}. "
            f"BT2 listening on port {self.bt_port}.",
        }

    @endpoints.register_method("trace.disconnect")
    async def disconnect(self) -> dict[Literal["status", "message"], str]:
        """
        Terminates the background read task and tears down transportation backend.

        Returns
        -------
        dict[Literal["status", "message"], str]
            Status message.
        """
        logger.info("Disconnecting")

        await self._live_trace_cleanup()

        return {"status": "success", "message": "Trace stopping initiated."}

    @endpoints.register_method("trace.stream_start")
    async def stream_start(self) -> dict[Literal["status"], str]:
        """
        Enables continuous trace streaming to the frontend.

        Returns
        -------
        dict[Literal["status"], str]
            Status message.
        """
        self.continuous_streaming = True
        logger.debug("Continuous streaming enabled.")
        return {"status": "success"}

    @endpoints.register_method("trace.stream_stop")
    async def stream_stop(self) -> dict[Literal["status"], str]:
        """
        Disables continuous trace streaming to the frontend.

        Returns
        -------
        dict[Literal["status"], str]
            Status message.
        """
        self.continuous_streaming = False
        logger.debug("Continuous streaming disabled.")
        return {"status": "success"}

    @endpoints.register_method("trace.metadata")
    async def metadata(self) -> dict[Literal["status", "message", "data"], Union[str, dict]]:
        """
        Provides model metadata and memory symbols for the trace.

        Returns
        -------
        dict[Literal["status", "message", "data"], Union[str, dict]]
            Message with metadata events or error.
        """
        logger.info("Collecting trace metadata")

        try:
            tef_metadata_events = []
            zephyr_elf_path = self.build_dir / "zephyr" / "zephyr.elf"

            if zephyr_elf_path.exists():
                self.symbol_map.clear()
                self.symbol_map.update(extract_symbol_map(zephyr_elf_path))

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
                logger.warning(f"Zephyr ELF not found at {zephyr_elf_path}.")

            if self.tflm_model_paths:
                logger.debug("Adding TFLM model metadata.")
                from extract_tflite_model_data import extract_model_data

                for tflm_model_path in self.tflm_model_paths:
                    if tflm_model_path.exists():
                        metadata = extract_model_data(
                            tflm_model_path, ZEPHYR_BASE, zephyr_elf_path, None
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

    @endpoints.register_method("trace.reset")
    async def reset(self):
        """Resets the trace buffer."""
        await self._execute_reset()
        return {"status": "success", "message": "Trace reset executed."}

    @endpoints.register_method("trace.collect")
    async def collect(self) -> dict[Literal["status", "message", "data"], Union[str, dict]]:
        """
        Provides the increment of the trace buffer not yet sent.

        Returns
        -------
        dict[Literal["status", "message", "data"], Union[str, dict]]
            Message with all events present in the buffer or error.
        """
        logger.info("Collecting trace increment")

        if len(self.pending_events) == 0:
            logger.warning("No trace data available to collect.")
            return {"status": "error", "message": "No trace data available to collect."}

        if self.continuous_streaming:
            logger.warning("Can't collect data while streaming.")
            return {"status": "error", "message": "Can't collect data while streaming."}

        try:
            events, metadata = self.pending_events[:], list(self.pending_metadata)
            self.pending_events.clear()
            self.pending_metadata.clear()

            await self.sio.emit(
                "rpc_notification",
                {
                    "jsonrpc": "2.0",
                    "method": "trace.events",
                    "params": {
                        "events": metadata + events,
                        "overlap_count": 0,
                        "total_count": len(self.trace_events),
                    },
                },
            )
            return {"status": "success"}

        except Exception as e:
            logger.error(f" Trace collection parse error: {e}")
            return {"status": "error", "message": f"Failed to parse trace file: {e}"}

    async def _cancel_all_tasks(self) -> None:
        """
        Cancels all async tasks and stops the CTF converter.
        Used by both full cleanup and soft reset.
        """
        if self.ctf_tef is not None:
            self.ctf_tef.stop()
            self.ctf_tef = None

        if self.ctf_tef_task is not None:
            self.ctf_tef_task.cancel()
            try:
                await self.ctf_tef_task
            except asyncio.CancelledError:
                pass
            self.ctf_tef_task = None

        if self.tef_task is not None:
            self.tef_task.cancel()
            try:
                await self.tef_task
            except asyncio.CancelledError:
                pass
            self.tef_task = None

        if self._emit_task is not None:
            self._emit_task.cancel()
            try:
                await self._emit_task
            except asyncio.CancelledError:
                pass
            self._emit_task = None
            self._emit_queue = None

    async def _live_trace_cleanup(self) -> bool:
        """
        Cleans up the state of the live tracing and tears down all resources.

        Returns
        -------
        bool
            Cleanup status.
        """
        if self.interceptor_server is not None:
            self.interceptor_server.close()
            await self.interceptor_server.wait_closed()
            self.interceptor_server = None

        if self.interceptor_task is not None:
            self.interceptor_task.cancel()
            try:
                await self.interceptor_task
            except asyncio.CancelledError:
                pass
            self.interceptor_task = None

        if self.bt2_thread:
            self.bt2_thread_stop = True
            await asyncio.get_event_loop().run_in_executor(None, self.bt2_thread.join)

            await self._cancel_all_tasks()

            self.pending_events = []
            self.pending_metadata = []
            self.bt2_thread = None
            self.trace_events = []
            self.bt2_thread_stop = False
            self.continuous_streaming = False
            self.msg_it = None
            gc.collect()

        return True

    async def _extract_trace_increment(self) -> tuple[list, list]:
        """
        Parses the CTF queue and formats thread metadata.

        Returns
        -------
        tuple[list, list]
            TEF events, total count of events.
        """
        if self.ctf_tef is None:
            self.ctf_tef = stream_ctf_to_tef(
                self.async_q,
                custom_metadata=CUSTOM_METADATA,
                custom_events=create_custom_events(
                    tvm_op_remove_prefix=self.tvm_op_remove_prefix,
                    tvm_op_remove_suffix=self.tvm_op_remove_suffix,
                    multi_model_trace=self.multi_model_trace,
                    symbol_map=self.symbol_map,
                ),
            )
            self.ctf_tef_task = self.ctf_tef.start()

        result = await self.ctf_tef.output_queue.get()
        new_trace_events, thread_names = result.tef, result.thread_names
        if self.tvm_model_paths:
            if 0 in MODEL_IDS_MAPPING:
                MODEL_IDS_MAPPING.pop(0)

            new_trace_events, tvm_prefix_to_model_id = tvm_recalculate_model_numbers(
                new_trace_events, len(MODEL_IDS_MAPPING)
            )

            MODEL_IDS_MAPPING.update(tvm_prefix_to_model_id)
            self.tvm_prefix_to_model_id.update(tvm_prefix_to_model_id)

        self.trace_events.extend(new_trace_events)

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

        return new_trace_events, new_metadata

    async def _parse_and_emit_diff(self):
        """
        Consumes parsed TEF events from the converter, maintains a sorted
        pending buffer, and pushes batches to the emit queue.
        """
        cooldown = 0.25
        last_emit = 0.0
        self.pending_events = []
        self.pending_metadata = collections.deque()
        try:
            while not self.bt2_thread_stop:
                try:
                    new_events, new_metadata = await self._extract_trace_increment()
                except Exception as e:
                    if "LTTNG_CTF_LTTNG_INDEX" not in str(e):
                        logger.error(f"Incremental parse error: {e}")
                    continue

                # Sort incoming batch by ts once, then merge-scan into pending list
                new_events.sort(key=lambda x: x["ts"])
                merged = []
                i = j = 0
                while i < len(self.pending_events) and j < len(new_events):
                    if self.pending_events[i]["ts"] <= new_events[j]["ts"]:
                        merged.append(self.pending_events[i])
                        i += 1
                    else:
                        merged.append(new_events[j])
                        j += 1
                merged.extend(self.pending_events[i:])
                merged.extend(new_events[j:])
                self.pending_events = merged

                self.pending_metadata.extend(new_metadata)

                now = time.monotonic()

                if now - last_emit >= cooldown and self.continuous_streaming:
                    to_send = max(1, len(self.pending_events) // 2)
                    batch = list(self.pending_metadata) + self.pending_events[:to_send]
                    self.pending_metadata.clear()
                    del self.pending_events[:to_send]

                    await self._emit_queue.put({
                        "type": "events",
                        "events": batch,
                    })
                    last_emit = now
                else:
                    await self._emit_queue.put({
                        "type": "status",
                    })
        except asyncio.CancelledError:
            # Flush remaining pending events before cancellation.
            if self.pending_events or self.pending_metadata:
                batch = list(self.pending_metadata) + self.pending_events
                self.pending_events.clear()
                self.pending_metadata.clear()
                try:
                    await self._emit_queue.put({
                        "type": "events",
                        "events": batch,
                    })
                except Exception as e:
                    logger.error(f"Final flush error: {e}")

    async def _emit_loop(self):
        """
        Background task that reads from _emit_queue and performs Socket.IO
        emits. Runs independently so async I/O doesn't block the consumer loop.
        """
        while True:
            msg = await self._emit_queue.get()

            if msg["type"] == "events":
                with self.trace_lock:
                    try:
                        await self.sio.emit(
                            "rpc_notification",
                            {
                                "jsonrpc": "2.0",
                                "method": "trace.events",
                                "params": {
                                    "events": msg["events"],
                                    "total_count": len(self.trace_events),
                                },
                            },
                        )
                    except Exception as e:
                        logger.error(f"Emit error: {e}")
            elif msg["type"] == "status":
                try:
                    await self.sio.emit(
                        "rpc_notification",
                        {
                            "jsonrpc": "2.0",
                            "method": "trace.status",
                            "params": {
                                "total_count": len(self.trace_events),
                            },
                        },
                    )
                except Exception as e:
                    logger.error(f"Status emit error: {e}")

    async def _raw_trace_interceptor(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """
        Receives raw bytes from the capture script, passes them
        through the CTFPacketFramer, and feeds clean data to babeltrace2.
        """
        logger.info("Capture script connected to interceptor.")
        proxy = StreamParserProxy()
        bt2_writer = None

        try:
            _, bt2_writer = await asyncio.open_connection("127.0.0.1", self.bt_port)
            logger.info("Interceptor connected to BT2 socket.")

            while not self.bt2_thread_stop:
                data = await reader.read(DATA_CHUNK_BYTES)
                if not data:
                    break

                for action, payload in proxy.process_data(data):
                    if action == "RESET":
                        await self._execute_reset()

                    elif action == "PACKET" and bt2_writer and payload:
                        bt2_writer.write(payload)
                        await bt2_writer.drain()

        except Exception as e:
            logger.error(f"Interceptor proxy error: {e}")
        finally:
            if bt2_writer:
                bt2_writer.close()
                await bt2_writer.wait_closed()
            writer.close()
            await writer.wait_closed()
            logger.info("Interceptor disconnected.")

    async def _execute_reset(self):
        """
        Clears the backend state, flushes the parsed event queue,
        and notifies the frontend to wipe the UI.
        """
        logger.info("Trace reset triggered. Clearing state.")

        await self._cancel_all_tasks()

        self._init_emit()
        self.tef_task = asyncio.create_task(self._parse_and_emit_diff())

        with self.trace_lock:
            self.trace_events.clear()
            self.pending_events.clear()
            self.pending_metadata.clear()
            self.trace_threads.clear()

            while self.async_q is not None and not self.async_q.empty():
                try:
                    self.async_q.get_nowait()
                except asyncio.QueueEmpty:
                    break

        try:
            await self.sio.emit(
                "rpc_notification",
                {
                    "jsonrpc": "2.0",
                    "method": "trace.reset",
                    "params": {},
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit trace.reset RPC: {e}")
