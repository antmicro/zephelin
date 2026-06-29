# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Mock Zephelin Server.

Allows to stream provided TEF file.
"""

import asyncio
import json
import logging
import os

import socketio

BUFFER_WINDOW_US = 16_000
INITIAL_DELAY_SEC = 0.5


def create_mock_socketio(trace_file_path: str | None = None, playback_speed: float = 1.0):
    """
    Creates and configures the mock asynchronous server.
    """
    sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

    state = {"active_client_sid": None, "stream_task": None, "accumulated_count": 0}

    metadata_events = []
    playback_events = []

    if trace_file_path and os.path.exists(trace_file_path):
        logging.info(f"[MockServer] Loading trace file: {trace_file_path}")
        with open(trace_file_path, "r") as f:
            data = json.load(f)
            raw_events = data.get("traceEvents", data) if isinstance(data, dict) else data

            for ev in raw_events:
                if ev.get("ph") == "M" and "ts" not in ev:
                    metadata_events.append(ev)
                elif "ts" in ev:
                    playback_events.append(ev)

        playback_events.sort(key=lambda x: x.get("ts", 0))
        logging.info(
            f"[MockServer] Loaded {len(metadata_events)} Metadata events"
            f" and {len(playback_events)} Trace events."
        )
    else:
        logging.warning("[MockServer] No valid trace file provided. Streaming will be empty.")

    async def clear_stream():
        if state["stream_task"] and not state["stream_task"].done():
            state["stream_task"].cancel()
            state["stream_task"] = None
            logging.info("[MockServer] Playback loop cancelled.")

    async def stream_file_data(sid):
        try:
            if not playback_events:
                return

            await asyncio.sleep(INITIAL_DELAY_SEC)

            event_buffer = []
            anchor_ts = playback_events[0]["ts"]

            for ev in playback_events:
                current_ts = ev["ts"]
                delta_us = current_ts - anchor_ts

                if delta_us < BUFFER_WINDOW_US:
                    event_buffer.append(ev)
                    continue

                state["accumulated_count"] += len(event_buffer)
                await sio.emit(
                    "rpc_notification",
                    {
                        "jsonrpc": "2.0",
                        "method": "trace.events",
                        "params": {
                            "events": event_buffer,
                            "total_count": state["accumulated_count"],
                        },
                    },
                    to=sid,
                )

                sleep_sec = (delta_us / 1_000_000.0) / playback_speed
                await asyncio.sleep(sleep_sec)

                anchor_ts = current_ts
                event_buffer = [ev]

            if event_buffer:
                state["accumulated_count"] += len(event_buffer)
                await sio.emit(
                    "rpc_notification",
                    {
                        "jsonrpc": "2.0",
                        "method": "trace.events",
                        "params": {
                            "events": event_buffer,
                            "total_count": state["accumulated_count"],
                        },
                    },
                    to=sid,
                )

            logging.info("[MockServer] Replay complete.")

        except asyncio.CancelledError:
            pass

    @sio.event
    async def connect(sid, environ):
        logging.info(f"[MockServer] Webview connected. SID: {sid}")
        state["active_client_sid"] = sid

    @sio.event
    async def disconnect(sid):
        if state["active_client_sid"] == sid:
            state["active_client_sid"] = None
            await clear_stream()

    @sio.event
    async def rpc_request(sid, req):
        method = req.get("method")

        if method == "trace.connect":
            await sio.emit(
                "rpc_response",
                {
                    "result": {
                        "status": "success",
                        "message": "Connected",
                    },
                },
                to=sid,
            )

        elif method == "trace.collect":
            pass

        elif method == "trace.metadata":
            await sio.emit(
                "rpc_response",
                {
                    "result": {
                        "status": "success",
                        "data": {
                            "events": metadata_events,
                            "total_count": len(metadata_events),
                        },
                    },
                },
                to=sid,
            )
            logging.info("[MockServer] Sent file metadata.")

        elif method == "trace.stream_start":
            await sio.emit("rpc_response", {"result": {"status": "success"}}, to=sid)
            await clear_stream()
            state["accumulated_count"] = 0
            state["stream_task"] = asyncio.create_task(stream_file_data(sid))
            logging.info(f"[MockServer] Playback started at {playback_speed}x speed.")

        elif method == "trace.stream_stop":
            await sio.emit("rpc_response", {"result": {"status": "success"}}, to=sid)
            await clear_stream()

    return sio
