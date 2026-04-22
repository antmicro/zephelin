# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Tests trace handling related functionalities."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.append(str(Path.cwd() / "server"))
sys.path.append(str(Path.cwd() / "scripts"))
from config import TraceConfig
from handlers.trace_handler import PARSE_THRESHOLD_BYTES, TraceHandler


@pytest.fixture
def trace_config(tmp_path):
    """Returns dummy config."""
    return TraceConfig(tcp_host="127.0.0.1", tcp_port=0, build_dir=tmp_path)


@pytest.mark.asyncio
@patch("handlers.trace_handler.TraceHandler._extract_trace_increment")
async def test_trace_ingestion_and_emit(mock_extract, trace_config, tmp_path):
    """Tests trace handling flow from ingesting data to emitting events."""
    fake_parsed_events = [{"name": "fake_event", "ts": 100}]

    mock_sio = AsyncMock()

    handler = TraceHandler(sio=mock_sio, traceConfig=trace_config)
    handler.continuous_streaming = True
    handler.raw_ctf_path = tmp_path / "live_capture.ctf"

    async def fake_extract_logic(update_state=False):
        if update_state:
            handler.events_sent_count = 1
        return (fake_parsed_events, 0, 1)

    mock_extract.side_effect = fake_extract_logic

    await handler.connect()
    writer = None

    try:
        host, port = handler.trace_socket.sockets[0].getsockname()
        _, writer = await asyncio.open_connection(host, port)

        sync_tag = b"_zpl_ctf_start__"

        fake_chunk = b"X" * (PARSE_THRESHOLD_BYTES * 2)

        writer.write(sync_tag + fake_chunk)
        await writer.drain()

        await asyncio.sleep(0.1)

        assert handler.is_synced is True
        assert handler.raw_ctf_path.exists()

        expected_size = PARSE_THRESHOLD_BYTES * 2 - len(sync_tag)
        assert handler.raw_ctf_path.stat().st_size == expected_size

        mock_sio.emit.assert_called_once_with(
            "rpc_notification",
            {
                "jsonrpc": "2.0",
                "method": "trace.events",
                "params": {
                    "events": fake_parsed_events,
                    "overlap_count": 0,
                    "total_count": 1,
                },
            },
        )

    finally:
        if writer is not None:
            writer.close()
            await writer.wait_closed()
        await handler.disconnect()
