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
import re
import sys
from pathlib import Path
from typing import Optional

import socketio
import uvicorn
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from config import TraceConfig  # noqa: E402
from extract_tvm_model_data import DEFAULT_OP_PREFIX_RE, DEFAULT_OP_SUFFIX_RE  # noqa: E402
from frontend import create_app  # noqa: E402
from socket_factory import create_socketio  # noqa: E402
from utils.logger import string_to_verbosity  # noqa: E402

load_dotenv()

logger = logging.getLogger("Backend")


def parse_env_path_list(env_var_name: str) -> Optional[list]:
    """Helper to parse comma-separated paths from environment variables."""
    val = os.environ.get(env_var_name)

    return [Path(p.strip()) for p in val.split(",")] if val else None


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
    # prepare_trace related options
    parser.add_argument(
        "--build-dir",
        type=Path,
        help="Path to the build directory",
        default=Path(os.environ.get("ZEPHELIN_BUILD_DIR", "build")),
    )
    parser.add_argument(
        "--tflm-model-paths",
        type=Path,
        nargs="+",
        help="Paths to TFLM models",
        default=parse_env_path_list("ZEPHELIN_TFLM_MODEL_PATHS"),
    )
    parser.add_argument(
        "--tvm-model-paths",
        type=Path,
        nargs="+",
        help="Paths to TVM models",
        default=parse_env_path_list("ZEPHELIN_TVM_MODEL_PATHS"),
    )
    parser.add_argument(
        "--tvm-model-metadata-paths",
        type=Path,
        nargs="+",
        help="Paths to TVM models metadata",
        default=parse_env_path_list("ZEPHELIN_TVM_MODEL_METADATA_PATHS"),
    )
    parser.add_argument(
        "--tvm-model-op-remove-prefix",
        type=re.compile,
        help="Pattern removing TVM operator prefix",
        default=os.environ.get("ZEPHELIN_TVM_DEFAULT_OP_PREFIX_RE", DEFAULT_OP_PREFIX_RE),
    )
    parser.add_argument(
        "--tvm-model-op-remove-suffix",
        type=re.compile,
        help="Pattern removing TVM operator type suffix",
        default=os.environ.get("ZEPHELIN_TVM_DEFAULT_OP_SUFFIX_RE", DEFAULT_OP_SUFFIX_RE),
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
        build_dir=args.build_dir,
        tflm_model_paths=args.tflm_model_paths,
        tvm_model_paths=args.tvm_model_paths,
        tvm_model_metadata_paths=args.tvm_model_metadata_paths,
        tvm_model_op_remove_prefix=args.tvm_model_op_remove_prefix,
        tvm_model_op_remove_suffix=args.tvm_model_op_remove_suffix,
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
