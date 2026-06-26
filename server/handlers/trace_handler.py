# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides a handler for trace collection related tasks.
"""

import asyncio
import gc
import json
import logging
import time
from pathlib import Path
from threading import Lock, Thread
from typing import Literal, Union

import bt2
from config import TraceConfig
from ctf2tef import stream_ctf_to_tef
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PARSE_THRESHOLD_BYTES = 8192

logger = logging.getLogger("TraceHandler")


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

        self.raw_ctf_path = Path("live_capture.ctf")
        self.events_sent_count = 0
        self.unprocessed_bytes = 0

        self.sync_tag = b"_zpl_ctf_start__"
        self.is_synced = False
        self.sync_buffer = bytearray()
        self.trace_threads = {}

        # Prevents 2 threads from reading CTF file at the same time

        self.continuous_streaming = False
        self.bt2_thread = None
        self.bt2_thread_stop = False
        self.diff_future = None
        self.trace_lock = Lock()
        self.msg_it = None

    @endpoints.register_method("trace.connnect")
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
            self.msg_it = bt2.TraceCollectionMessageIterator(
                bt2.ComponentSpec(
                    dummy_cc,
                    {"port": self.bt_port},
                ),
                live_mode=True,
            )

            # Iterate the trace messages.
            while not self.bt2_thread_stop:
                try:
                    msg = next(self.msg_it)
                    asyncio.run_coroutine_threadsafe(
                        self.async_q.put(msg), self.async_loop
                    ).result()
                except bt2.TryAgain:
                    # To avoid keeping the thread pinned at 100% all the time
                    # At the same time, the delay has to be small enough to avoid
                    # Issues with message throttling on the socket
                    time.sleep(0.001)
                    continue

        self.bt2_thread = Thread(target=do_stream)
        self.bt2_thread.start()
        self.tef_task = asyncio.create_task(self._parse_and_emit_diff())

        logger.info(" BT2 Listening for trace streams on port " + str(self.bt_port))
        return {
            "status": "success",
            "message": " BT2 Listening for trace streams on port " + str(self.bt_port),
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

        await self.live_trace_cleanup()

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
        logger.debug("Continous streaming enabled.")
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
        logger.debug("Continous streaming disabled.")
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
            with self.trace_lock:
                await self.sio.emit(
                    "rpc_notification",
                    {
                        "jsonrpc": "2.0",
                        "method": "trace.events",
                        "params": {
                            "events": self.pending_events,
                            "overlap_count": 0,
                            "total_count": len(self.trace_events),
                        },
                    },
                )
                self.pending_events = []

            return {"status": "success"}

        except Exception as e:
            logger.error(f" Trace collection parse error: {e}")
            return {"status": "error", "message": f"Failed to parse trace file: {e}"}

    async def live_trace_cleanup(self) -> bool:
        """
        Cleans up the state of the live tracing.

        Returns
        -------
        bool
            Cleanup status.
        """
        if self.bt2_thread:
            self.bt2_thread_stop = True
            await asyncio.get_event_loop().run_in_executor(None, self.bt2_thread.join)
            self.tef_task.cancel()
            await self.tef_task

            self.pending_events = []
            self.bt2_thread = None
            self.trace_events = []
            self.tef_task = None
            self.bt2_thread_stop = False
            self.events_sent_count = 0
            self.continuous_streaming = False
            self.msg_it = None
            gc.collect()

        return True

    async def _extract_trace_increment(self) -> tuple[list, int]:
        """
        Parses the CTF queue and formats thread metadata.

        Returns
        -------
        tuple[list, int]
            TEF events, total count of events.
        """
        new_trace_events, thread_names = await anext(
            stream_ctf_to_tef(
                self.async_q,
                custom_metadata=CUSTOM_METADATA,
                custom_events=create_custom_events(
                    tvm_op_remove_prefix=self.tvm_op_remove_prefix,
                    tvm_op_remove_suffix=self.tvm_op_remove_suffix,
                    multi_model_trace=self.multi_model_trace,
                    symbol_map=self.symbol_map,
                ),
            )
        )
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

        return new_trace_events, new_metadata, len(new_trace_events)

    async def _parse_and_emit_diff(self):
        """
        Converts CTF data in the buffer file into TEF and emits events that were not previously
        emitted.
        """
        cooldown = 0.1
        last_emit = 0.0
        self.pending_events = []
        self.pending_metadata = []
        while not self.bt2_thread_stop:
            try:
                new_events, new_metadata, _ = await self._extract_trace_increment()
                self.pending_events.extend(new_events)
                self.pending_metadata.extend(new_metadata)
                self.pending_events.sort(key=lambda x: x["ts"])

                now = time.monotonic()

                if now - last_emit >= cooldown and self.continuous_streaming:
                    # Currently on renode the cooldown will gather ~25 events on the tested example
                    # this method of avoiding unsorted events is faulty,
                    # when an event is heavily delayed, it will be sent out of order.
                    # To mitigate this, one can either increase the cooldown, or
                    # add more sophisticated chunking logic, eg sending packets of 50
                    # traces or after a much more substantial timeout
                    to_send = int(len(self.pending_events) / 2)
                    with self.trace_lock:
                        await self.sio.emit(
                            "rpc_notification",
                            {
                                "jsonrpc": "2.0",
                                "method": "trace.events",
                                "params": {
                                    "events": self.pending_metadata + self.pending_events[:to_send],
                                    "overlap_count": 0,
                                    "total_count": len(self.trace_events),
                                },
                            },
                        )
                        self.pending_events = self.pending_events[to_send:]
                        self.pending_metadata = []
                        last_emit = now
                else:
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
                # It is expected that some parsed events will be incomplete
                if "LTTNG_CTF_LTTNG_INDEX" not in str(e):
                    logger.error(f"Incremental parse error: {e}")
            except asyncio.CancelledError:
                break

    async def _execute_reset(self):
        """
        Clears the backend state, flushes the parsed event queue,
        and notifies the frontend to wipe the UI.
        """
        logger.info("Trace reset triggered. Clearing state.")

        with self.trace_lock:
            self.trace_events.clear()
            self.pending_events.clear()
            self.pending_metadata.clear()
            self.trace_threads.clear()

            while not self.async_q.empty():
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
