# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides the entry point for starting the Zephelin trace gathering server.
"""

import argparse
import os
import sys
from pathlib import Path

import socketio
import uvicorn
from config import TraceConfig
from dotenv import load_dotenv
from frontend import create_app
from socket_factory import create_socketio

load_dotenv()


def create_backend(argv):
    """
    Initializes backend components.
    """
    parser = argparse.ArgumentParser(argv[0], allow_abbrev=False)
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

    args, _ = parser.parse_known_args(argv[1:])

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

    print(f"Statring Zephelin Server and ZTV on http://{args.backend_host}:{args.backend_port}")

    uvicorn.run(
        asgi_app,
        host=args.backend_host,
        port=args.backend_port,
    )


if __name__ == "__main__":
    main(sys.argv)
