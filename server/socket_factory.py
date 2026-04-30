# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides a shared Socket.IO instance for the Zephelin server.
"""

import logging

import socketio
from config import TraceConfig
from handlers.trace_handler import TraceHandler
from rpc_dispatcher import RPCDispatcher

logger = logging.getLogger("Backend")


def create_socketio(traceConfig: TraceConfig) -> socketio.AsyncServer:
    """
    Creates and configures the python-socketio asynchronous server.
    """
    sio = socketio.AsyncServer(
        async_mode="asgi",
        cors_allowed_origins="*",
    )

    dispatcher = RPCDispatcher()

    trace_backend = TraceHandler()
    dispatcher.register_methods(trace_backend, namespace="trace")

    @sio.on("connect")
    async def connect(sid: str, environ: dict):
        """
        Handles new client connections.
        """
        logger.info(f"Client {sid} connected.")

    @sio.on("disconnect")
    async def disconnect(sid):
        """
        Handles client disconnection.
        """
        logger.info(f"Client {sid} disconnected.")

    @sio.on("rpc_request")
    async def handle_rpc(sid, data):
        """
        Routes incoming JSON-RPC requests to the dispatcher.
        """
        logger.info(f"Request from {sid}: {data.get('method', 'Unknown Method')}")
        response = await dispatcher.dispatch_rpc(data)

        if response is not None:
            await sio.emit("rpc_response", response, to=sid)

    return sio
