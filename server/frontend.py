# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides functions for creating the FastAPI frontend application.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def create_app(frontend_dir: Path) -> FastAPI:
    """
    Hosts frontend application.

    Parameters
    ----------
    frontend_dir: Path
        Path where the frontend build is stored.

    Returns
    -------
    FastAPI
        FastAPI instance.
    """
    app = FastAPI(title="Zephelin Trace Viewer")

    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")

    return app
