# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides functions for creating the FastAPI frontend application.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from handlers.trace_handler import TraceHandler


def create_app(frontend_dir: Path, trace_backend: TraceHandler) -> FastAPI:
    """
    Hosts frontend application.

    Parameters
    ----------
    frontend_dir: Path
        Path where the frontend build is stored.
    trace_backend: TraceHandler
        Instance of trace handler that requires context management

    Returns
    -------
    FastAPI
        FastAPI instance.
    """

    @asynccontextmanager
    async def lifespan(app):
        yield
        if trace_backend is not None:
            await trace_backend._live_trace_cleanup()

    app = FastAPI(title="Zephelin Trace Viewer", lifespan=lifespan)

    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")

    return app
