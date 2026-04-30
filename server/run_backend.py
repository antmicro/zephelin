# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Zephelin Trace Gathering Server.

This script serves as the main entry point for the Zephelin backend.
It initializes a TCP server for ingesting CTF traces, and hosts
a Zephelin Trace Viewer instance where traces can be visualized.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import socketio
import uvicorn
from config import TraceConfig
from dotenv import load_dotenv
from frontend import create_app
from socket_factory import create_socketio
from utils.logger import string_to_verbosity

load_dotenv()

logger = logging.getLogger("Backend")


def create_backend(argv):
    """
    Initializes backend components.
    """
    parser = argparse.ArgumentParser(
        argv[0],
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
    )
    parser.add_argument(
        "--tcp-server-host",
        type=str,
        help="Address of the Zephelin TCP Server (CTF trace ingestion)",
        default=os.environ.get("ZEPHELIN_TCP_HOST", "127.0.0.1"),
    )
    parser.add_argument(
        "--tcp-server-port",
        type=int,
        help="Port of the Zephelin TCP server (CTF trace ingestion)",
        default=os.environ.get("ZEPHELIN_TCP_PORT", 5000),
    )
    parser.add_argument(
        "--backend-host",
        type=str,
        help="Address of the Zephelin backend",
        default=os.environ.get("ZEPHELIN_BACKEND_HOST", "127.0.0.1"),
    )
    parser.add_argument(
        "--backend-port",
        type=int,
        help="Port of the Zephelin backend",
        default=os.environ.get("ZEPHELIN_BACKEND_PORT", 8000),
    )

    frontend_dir_env = os.environ.get("ZEPHELIN_FRONTEND_DIR")
    parser.add_argument(
        "--frontend-directory",
        type=Path,
        help="Path to the fronetend build",
        default=Path(frontend_dir_env) if frontend_dir_env else None,
    )

    parser.add_argument(
        "--verbosity",
        help="Verbosity level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        type=str,
    )

    args, _ = parser.parse_known_args(argv[1:])
    logging.basicConfig(
        level=string_to_verbosity(args.verbosity), format="[%(levelname)s][%(name)s] %(message)s"
    )

    traceConfig = TraceConfig(
        tcp_host=args.tcp_server_host,
        tcp_port=args.tcp_server_port,
    )

    sio = create_socketio(traceConfig=traceConfig)

    app = create_app(args.frontend_directory)

    asgi_app = socketio.ASGIApp(sio, other_asgi_app=app)

    return asgi_app, args


def main(argv):  # noqa: D103
    asgi_app, args = create_backend(argv)

    logger.info(
        f"Statring Zephelin Server and Zephelin Trace Viewer "
        f"on http://{args.backend_host}:{args.backend_port}"
    )

    uvicorn.run(
        asgi_app,
        host=args.backend_host,
        port=args.backend_port,
    )


if __name__ == "__main__":
    main(sys.argv)
