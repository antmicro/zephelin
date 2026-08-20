# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Tests trace handling related functionalities."""

import asyncio
import contextlib
import itertools
import struct
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.append(str(Path.cwd() / "server"))
sys.path.append(str(Path.cwd() / "scripts"))

import prepare_trace
from config import TraceConfig
from handlers.trace_handler import (
    _CTF_TRACE_START_TAG,
    StreamParserProxy,
    TraceHandler,
)


def _packet(payload: bytes, size_is_bits: bool = True) -> bytes:
    """
    Builds a CTF-like packet whose header advertises its own length.
    """
    total = 4 + len(payload)
    size_field = total * 8 if size_is_bits else total
    return struct.pack("<HH", 0, size_field) + payload


def _drain(queue: asyncio.Queue) -> list:
    """
    Returns every item currently sitting on the queue.
    """
    items = []
    while not queue.empty():
        items.append(queue.get_nowait())
    return items


def test_proxy_discards_data_before_sync():
    """
    Data arriving before the sync tag yields nothing and is dropped,
    except enough to detect the tag across reads.
    """
    proxy = StreamParserProxy()
    out = list(proxy.process_data(b"x" * 100))

    assert out == []
    assert proxy.is_synced is False
    # Only a trailing window the size of the tag is retained for split detection.
    assert len(proxy.buffer) == len(_CTF_TRACE_START_TAG)


def test_proxy_sync_tag_yields_reset():
    """Encountering the sync tag yields a RESET and marks the proxy synced."""
    proxy = StreamParserProxy()
    out = list(proxy.process_data(b"ABCD" + _CTF_TRACE_START_TAG))

    assert out == [("RESET", None)]
    assert proxy.is_synced is True
    assert len(proxy.buffer) == 0


def test_proxy_single_full_packet():
    """After sync, a complete packet is emitted."""
    proxy = StreamParserProxy()
    packet = _packet(b"ABCD")
    out = list(proxy.process_data(_CTF_TRACE_START_TAG + packet))

    assert out == [("RESET", None), ("PACKET", packet)]
    assert len(out[1][1]) == 8
    assert proxy.expected_size is None
    assert len(proxy.buffer) == 0


def test_proxy_partial_packet_across_calls():
    """A packet split across reads is buffered until complete, then emitted."""
    proxy = StreamParserProxy()
    packet = _packet(b"ABCD")

    first = list(proxy.process_data(_CTF_TRACE_START_TAG + packet[:6]))
    assert first == [("RESET", None)]
    assert proxy.expected_size == 8

    second = list(proxy.process_data(packet[6:]))
    assert second == [("PACKET", packet)]


def test_proxy_multiple_packets_in_one_call():
    """Several packets in a single chunk are yielded sequentially."""
    proxy = StreamParserProxy()
    p1 = _packet(b"AAAA")
    p2 = _packet(b"BBBB")
    out = list(proxy.process_data(_CTF_TRACE_START_TAG + p1 + p2))

    assert out == [("RESET", None), ("PACKET", p1), ("PACKET", p2)]


def test_proxy_sync_tag_split_across_reads():
    """A sync tag split between two reads is still detected."""
    proxy = StreamParserProxy()
    half = len(_CTF_TRACE_START_TAG) // 2

    first = list(proxy.process_data(b"y" * 20 + _CTF_TRACE_START_TAG[:half]))
    assert first == []
    assert proxy.is_synced is False

    second = list(proxy.process_data(_CTF_TRACE_START_TAG[half:]))
    assert second == [("RESET", None)]
    assert proxy.is_synced is True


def test_proxy_corrupt_header_resyncs():
    """Drops the packet if it's to small."""
    proxy = StreamParserProxy()
    gen = proxy.process_data(_CTF_TRACE_START_TAG + struct.pack("<HH", 0, 0) + b"AAAA")

    out = list(itertools.islice(gen, 5))

    assert out == [("RESET", None)]
    assert proxy.expected_size is None
    assert proxy.is_synced is False
    assert len(proxy.buffer) == 0


@pytest.fixture(autouse=True)
def _reset_prepare_trace_globals():
    """Snapshots and restores mutable module globals mutated by the handler."""
    model_ids = dict(prepare_trace.MODEL_IDS_MAPPING)
    region_sizes = dict(prepare_trace.REGION_SIZES)
    yield
    prepare_trace.MODEL_IDS_MAPPING.clear()
    prepare_trace.MODEL_IDS_MAPPING.update(model_ids)
    prepare_trace.REGION_SIZES.clear()
    prepare_trace.REGION_SIZES.update(region_sizes)


@pytest.fixture
def trace_config(tmp_path):
    """Returns a minimal trace configuration pointing at an empty build dir."""
    return TraceConfig(tcp_host="127.0.0.1", tcp_port=0, build_dir=tmp_path)


@pytest.fixture
def handler(trace_config):
    """Builds a TraceHandler with a mocked socket.io server."""
    return TraceHandler(AsyncMock(), trace_config)


@pytest.mark.asyncio
async def test_metadata_reports_error_on_exception(handler):
    """Failures during metadata extraction are reported as an error status."""
    elf_path = handler.build_dir / "zephyr" / "zephyr.elf"
    elf_path.parent.mkdir(parents=True)
    elf_path.write_bytes(b"\x7fELF")

    handler._metadata_cache = None

    with patch(
        "handlers.trace_handler.extract_symbol_map",
        side_effect=RuntimeError("error"),
    ):
        result = await handler.metadata()

    assert result["status"] == "error"
    assert "error" in result["message"]


@pytest.mark.asyncio
async def test_metadata_returns_cached_events_without_recollecting(handler):
    """A populated cache is served directly, check if no collecting is happening."""
    handler._metadata_cache = [{"name": "MEMORY::SYMBOLS"}]

    with patch.object(handler, "_metadata_sync") as mock_sync:
        result = await handler.metadata()

    mock_sync.assert_not_called()
    assert result == {"status": "success", "data": {"events": [{"name": "MEMORY::SYMBOLS"}]}}


@pytest.mark.asyncio
async def test_collect_without_data_returns_error(handler):
    """Collecting with an empty buffer returns an error status."""
    handler.pending_events = []

    result = await handler.collect()

    assert result["status"] == "error"
    assert "No trace data" in result["message"]
    handler.sio.emit.assert_not_called()


@pytest.mark.asyncio
async def test_collect_while_streaming_returns_error(handler):
    """Collecting is refused while continuous streaming is active."""
    handler.pending_events = [{"ts": 1}]
    handler.continuous_streaming = True

    result = await handler.collect()

    assert result["status"] == "error"
    assert "streaming" in result["message"]
    handler.sio.emit.assert_not_called()


@pytest.mark.asyncio
async def test_collect_emits_pending_events(handler):
    """A successful collect emits pending events and clears the buffer."""
    handler.pending_events = [{"ts": 1}, {"ts": 2}]
    handler.trace_events = [{"ts": 1}, {"ts": 2}]

    result = await handler.collect()

    assert result == {"status": "success"}
    handler.sio.emit.assert_awaited_once()
    channel, payload = handler.sio.emit.await_args.args
    assert channel == "rpc_notification"
    assert payload["method"] == "trace.events"
    assert payload["params"]["events"] == [{"ts": 1}, {"ts": 2}]
    assert payload["params"]["total_count"] == 2
    assert handler.pending_events == []


@pytest.mark.asyncio
async def test_reset_clears_state_and_notifies(handler):
    """Reset wipes buffers, drains the queue, and emits a reset notification."""
    handler.async_q = asyncio.Queue()
    handler.async_q.put_nowait("stale")
    handler.trace_events = [{"ts": 1}]
    handler.pending_events = [{"ts": 1}]
    handler.pending_metadata = [{"name": "thread_name"}]
    handler.trace_threads = {1: "main"}

    result = await handler.reset()

    assert result["status"] == "success"
    assert handler.trace_events == []
    assert handler.pending_events == []
    assert handler.pending_metadata == []
    assert handler.trace_threads == {}
    assert handler.async_q.empty()

    handler.sio.emit.assert_awaited_once()
    _, payload = handler.sio.emit.await_args.args
    assert payload["method"] == "trace.reset"


@pytest.mark.asyncio
async def test_connect_keeps_existing_when_already_listening(handler):
    """A second connect while a bt2 thread exists keeps the current one."""
    handler.bt2_thread = object()

    result = await handler.connect()

    assert result["status"] == "success"
    assert "Already listening" in result["message"]


@pytest.mark.asyncio
async def test_disconnect_delegates_to_cleanup(handler):
    """Disconnect triggers live-trace cleanup and returns success."""
    handler._live_trace_cleanup = AsyncMock(return_value=True)

    result = await handler.disconnect()

    handler._live_trace_cleanup.assert_awaited_once()
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_parse_and_emit_diff_queues_status_when_not_streaming(handler):
    """Without streaming, the diff loop only queues a status message."""
    handler._emit_queue = asyncio.Queue()
    handler.continuous_streaming = False
    events = [{"ts": 2}, {"ts": 1}]

    async def fake_increment():
        handler.bt2_thread_stop = True
        return events, []

    with patch.object(handler, "_extract_trace_increment", side_effect=fake_increment):
        await handler._parse_and_emit_diff()

    assert [msg["type"] for msg in _drain(handler._emit_queue)] == ["status"]
    assert handler.pending_events == events


@pytest.mark.asyncio
async def test_emit_loop_maps_queued_messages_to_sio(handler):
    """The emit loop turns queued messages into Socket.IO notifications."""
    handler._emit_queue = asyncio.Queue()
    handler.trace_events = [{"ts": 1}, {"ts": 2}]
    handler._emit_queue.put_nowait({"type": "events", "events": [{"ts": 1}]})
    handler._emit_queue.put_nowait({"type": "status"})

    task = asyncio.create_task(handler._emit_loop())
    for _ in range(20):
        await asyncio.sleep(0)
        if handler.sio.emit.await_count >= 2:
            break
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    calls = handler.sio.emit.await_args_list
    assert [call.args[1]["method"] for call in calls] == ["trace.events", "trace.status"]
    assert calls[0].args[1]["params"]["events"] == [{"ts": 1}]
    assert calls[0].args[1]["params"]["total_count"] == 2
    assert calls[1].args[1]["params"]["total_count"] == 2
