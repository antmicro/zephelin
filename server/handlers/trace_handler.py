# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides a handler for trace collection related tasks.
"""

from handlers.base import BaseHandler


class TraceHandler(BaseHandler):
    """
    Handler responsible for managing the lifecycle of trace data collection.
    """

    async def connect(self):
        """Starts the TCP server to listen for incoming trace streams from capture scripts."""
        raise NotImplementedError
    def __init__(
        self,
    ):
        """
        Builds the TraceHandler.

    async def disconnect(self):
        """Terminates the background read task and tears down transportation backend."""
        raise NotImplementedError

        self.continuous_streaming = False

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

    async def collect(self):
        """Provides the increment of the trace buffer not yet sent."""
        raise NotImplementedError
