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

    async def disconnect(self):
        """Terminates the background read task and tears down transportation backend."""
        raise NotImplementedError

    async def stream_start(self):
        """Enables continuous trace streaming to the frontend."""
        raise NotImplementedError

    async def stream_stop(self):
        """Disables continuous trace streaming to the frontend."""
        raise NotImplementedError

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
