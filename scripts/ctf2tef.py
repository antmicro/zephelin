#!/usr/bin/env python3
# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0
"""
Script converting Common Trace Format (CTF) trace
to the JSON-based Trace Event Format (TEF), which can be consumed by Speedscope.
"""

import argparse
import asyncio
import collections
import json
import os
import sys
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from math import isnan
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory
from typing import Any, Callable, NamedTuple

import bt2  # From the babeltrace2 package.


class EventPhase(Enum):
    """
    Available phases in Trace Event Format.
    """

    BEGIN = "B"
    END = "E"
    # Events not supported by Speedscope
    COMPLETE = "X"
    INSTANT = "i"
    COUNTER = "C"
    NESTABLE_START = "b"
    NESTABLE_INSTANT = "n"
    NESTABLE_END = "e"
    FLOW_START = "s"
    FLOW_STEP = "t"
    FLOW_END = "f"
    SAMPLE = "P"
    OBJECT_CREATED = "N"
    OBJECT_SNAPSHOT = "O"
    OBJECT_DESTROYED = "D"
    METADATA = "M"
    MEMORY_DUMP_GLOBAL = "V"
    MEMORY_DUMP_PROCESS = "v"
    MARK = "R"
    CLOCK_SYNC = "c"
    CONTEXT_BEGIN = "("
    CONTEXT_END = ")"


@dataclass
class CustomEventDefinition:
    """
    Definition of custom event.

    Attributes
    ----------
    new_name : str
        The name of newly created event.
    enter_event_name : str
        The name of CTF event marking the start of new event.
    exit_event_name : str
        The name of CTF event marking the end of new event.
    suffix_func : Callable[[bt2._EventMessageConst], str] | None
        Optional function returning suffix of the new event based on its data.
    additional_arg_func : Callable[[bt2._EventMessageConst], str] | None
        Optional function returning additional arguments for the new event based on its data.
    """

    new_name: str
    enter_event_name: str
    exit_event_name: str
    suffix_func: Callable[[bt2._EventMessageConst], str] | None
    additional_arg_func: Callable[[bt2._EventMessageConst], str] | None


@dataclass
class CustomMetadataDefinition:
    """
    Definition of custom metadata event.

    Attributes
    ----------
    new_name : str
        The name of newly created event.
    suffix_func : Callable[[bt2._EventMessageConst], str] | None
        Optional function returning suffix of the new event based on its data.
    additional_arg_func : Callable[[bt2._EventMessageConst], str] | None
        Optional function returning additional arguments for the new event based on its data.
    """

    new_name: str
    suffix_func: Callable[[bt2._EventMessageConst], str] | None
    additional_arg_func: Callable[[bt2._EventMessageConst], str] | None


def extract_us(msg: bt2._EventMessageConst) -> float:
    """
    Extracts the timestamp of the event and converts it to microseconds.

    Parameters
    ----------
    msg : bt2._EventMessageConst
        Representation of the event message to be printed.

    Returns
    -------
    float
        The timestamp in microseconds.
    """
    assert msg.default_clock_snapshot.clock_class.frequency == 1e9
    ns = msg.default_clock_snapshot.value
    return ns * 1e-3


def convert_from_bt2(x: Any) -> str | int | float | bool | dict:
    """
    Converts data from bt2 format to serializable Python types.

    Parameters
    ----------
    x : Any
        The object that should be converted.

    Returns
    -------
    str | int | float | bool | dict
        The object converted to Python type.

    Raises
    ------
    ValueError
        Raised if type of the given object is not supported.
    """
    if isinstance(x, str | int | float):
        if isinstance(x, float) and isnan(x):
            return None
        return x
    if isinstance(x, dict | bt2._StructureFieldConst):
        return {convert_from_bt2(k): convert_from_bt2(v) for k, v in x.items()}
    if isinstance(x, bt2._StaticArrayFieldConst):
        return [convert_from_bt2(v) for v in x]
    if isinstance(x, bt2._BoolValueConst | bt2._BoolFieldConst):
        return bool(x)
    if isinstance(x, bt2._EnumerationFieldConst):
        return repr(x)
    if isinstance(x, bt2._IntegerValueConst | bt2._IntegerFieldConst):
        return int(x)
    if isinstance(x, bt2._RealValueConst | bt2._RealFieldConst):
        x = float(x)
        return None if isnan(x) else x
    if isinstance(x, bt2._StringValueConst | bt2._StringFieldConst):
        return str(x)
    if isinstance(x, collections.abc.Mapping):
        return {convert_from_bt2(k): convert_from_bt2(v) for k, v in x.items()}
    if isinstance(x, collections.abc.Sequence):
        return [convert_from_bt2(v) for v in x]
    raise ValueError("Unexpected value from trace", x, type(x))


def emit_event(
    name: str,
    tid: int,
    phase: EventPhase,
    ts_micros: float,
    payload_field=None,
    shift: float = 0,
    skip_args: bool = False,
    additional_args: dict | None = None,
):
    """
    Constructs a TEF event dict from pre-extracted values.

    Parameters
    ----------
    name : str
        The name of event.
    tid : int
        The thread ID.
    phase : EventPhase
        The event phase, usually either begin or end.
    ts_micros : float
        The timestamp in microseconds (pre-extracted).
    payload_field : bt2._StructureFieldConst | None
        Pre-extracted event payload field.
    shift : float
        The shift added to a timestamp.
    skip_args : bool
        Whether arguments should be skipped.
    additional_args : dict | None
        Additional data appended to "args".
    """
    result = {
        "name": name,
        "cat": "zephyr",
        "ph": phase.value,
        "ts": ts_micros + shift,
        "pid": 0,
        "tid": tid,
    }
    if not skip_args and payload_field:
        args = convert_from_bt2(payload_field)
        if additional_args:
            args.update(additional_args)
        result["args"] = args
    return result


class CTFConversionResult(NamedTuple):
    """
    The results of CTF to TEF conversion.
    """

    # Converted trace in TEF
    tef: list[dict]
    # Mapping of thread name to its ID
    thread_names: dict[str, int]


def _parse_msg(
    msg,
    thread_name,
    current_thread,
    custom_metadata,
    custom_event_begin,
    custom_event_end,
    custom_event_name_func,
    custom_event_args_func,
    skip_args,
):
    event = msg.event
    event_name = event.name
    payload_field = event.payload_field or {}

    ts_micros = msg.default_clock_snapshot.value * 1e-3
    thread_id = int(payload_field.get("thread_id", current_thread[payload_field.get("cpu_id", -1)]))

    ev_name = None
    ev_phase = None
    ev_additional_args = None
    # Process custom metadata
    if event_name in custom_metadata:
        m = custom_metadata[event_name]
        ev_name = f"{m.new_name}{m.suffix_func(msg) if m.suffix_func else ''}"
        ev_phase = EventPhase.METADATA
        ev_additional_args = m.additional_arg_func(msg) if m.additional_arg_func else {}
    # Process custom events
    elif event_name in custom_event_begin:
        ev_name = f"{custom_event_begin[event_name][0]}{custom_event_name_func[event_name](msg)}"
        ev_phase = EventPhase.BEGIN
        ev_additional_args = (
            custom_event_args_func[event_name](msg) if custom_event_args_func[event_name] else None
        )
    elif event_name in custom_event_end:
        ev_name = f"{custom_event_end[event_name][0]}{custom_event_name_func[event_name](msg)}"
        ev_phase = EventPhase.END
        ev_additional_args = (
            custom_event_args_func[event_name](msg) if custom_event_args_func[event_name] else None
        )
    # Process Zephyr events (starts with *_enter and finishes with *_exit)
    elif event_name.endswith("_enter"):
        ev_name = event_name[:-6]
        ev_phase = EventPhase.BEGIN
    elif event_name.endswith("_exit"):
        ev_name = event_name[:-5]
        ev_phase = EventPhase.END
    # Check whether thread has changed
    if str(event_name).startswith("thread_") and "thread_id" in payload_field:
        thread_name[str(payload_field["name"])] = int(payload_field["thread_id"])
    # Check whether thread has changed
    if event_name == "thread_switched_in":
        current_thread[payload_field["cpu_id"]] = thread_id = int(payload_field["thread_id"])

    if ev_name is not None:
        return emit_event(
            ev_name,
            thread_id,
            ev_phase,
            ts_micros,
            payload_field=event.payload_field,
            skip_args=skip_args,
            additional_args=ev_additional_args,
        )


class StreamingCTFToTEF:
    """
    Converts CTF trace to the JSON in TEF format using a background task.
    """

    def __init__(
        self,
        q: asyncio.Queue,
        skip_args: bool = False,
        custom_metadata: dict[str, CustomMetadataDefinition] | None = None,
        custom_events: list[CustomEventDefinition] | None = None,
        batch_size: int = 50,
        flush_interval_s: float = 0.01,
    ):
        """
        Initialize the converter and calculate custom events.

        Parameters
        ----------
        q : asyncio.Queue
            Incoming message queue.
        skip_args : bool
            Whether the arguments of events should be ignored.
        custom_metadata : dict[str, CustomMetadataDefinition] | None
            Dictionary mapping CTF event to the TEF metadata.
        custom_events : list[CustomEventDefinition] | None
            List with mapping of the beginning and the end represented by CTF events
            to a new TEF event.
        batch_size : int
            Number of messages to accumulate before flushing.
        flush_interval_s : float
            Maximum time (seconds) to wait before flushing regardless of batch size.

        Returns
        -------
        StreamingCTFToTEF
            Instance with an ``output_queue`` attribute yielding CTFConversionResult objects.
        """
        if custom_metadata is None:
            custom_metadata = {}
        if custom_events is None:
            custom_events = []

        self._input_queue = q
        self._custom_metadata = custom_metadata
        self._skip_args = skip_args
        self._batch_size = batch_size
        self._flush_interval_s = flush_interval_s

        custom_event_begin = defaultdict(list)
        custom_event_end = defaultdict(list)
        custom_event_name_func = {}
        custom_event_args_func = {}

        for e in custom_events:
            custom_event_begin[e.enter_event_name].append(e.new_name)
            custom_event_end[e.exit_event_name].append(e.new_name)
            custom_event_name_func[e.enter_event_name] = e.suffix_func
            custom_event_name_func[e.exit_event_name] = e.suffix_func
            custom_event_args_func[e.enter_event_name] = e.additional_arg_func
            custom_event_args_func[e.exit_event_name] = e.additional_arg_func

        self._custom_event_begin = custom_event_begin
        self._custom_event_end = custom_event_end
        self._custom_event_name_func = custom_event_name_func
        self._custom_event_args_func = custom_event_args_func

        self._thread_name: dict[str, int] = {}
        self._current_thread = defaultdict(int)
        self._converted: list[dict] = []
        self._batch: list = []
        self._last_flush = time.perf_counter()

        self.output_queue: asyncio.Queue[CTFConversionResult] = asyncio.Queue()
        self._task: asyncio.Task | None = None
        self.checked_timebase = False

    def start(self) -> asyncio.Task:
        """Start the background conversion task. Returns the task handle."""
        self._task = asyncio.create_task(self._run())
        return self._task

    def stop(self) -> None:
        """Signal the background task to stop and cancel it."""
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _run(self) -> None:
        try:
            while True:
                # Use a timeout on the queue get so we can periodically check
                # if a partial batch needs flushing when input pauses or stops.
                try:
                    item = await asyncio.wait_for(
                        self._input_queue.get(), timeout=self._flush_interval_s
                    )
                    if isinstance(item, tuple):
                        self._batch.extend(item)
                    else:
                        self._batch.append(item)
                except asyncio.TimeoutError:
                    pass

                now = time.perf_counter()
                should_flush = len(self._batch) >= self._batch_size
                # Flush partial batch if we've been idle long enough since last item arrived
                if not should_flush and self._batch:
                    should_flush = (now - self._last_flush) >= self._flush_interval_s

                if should_flush:
                    self._converted.extend(self._parse_batch(self._batch))
                    self._batch.clear()
                    self._last_flush = now

                    if self._converted:
                        await self.output_queue.put(
                            CTFConversionResult(self._converted, dict(self._thread_name))
                        )
                        self._converted = []
        except asyncio.CancelledError:
            # Flush remaining messages on cancellation before exiting.
            if self._batch:
                self._converted.extend(self._parse_batch(self._batch))
                self._batch.clear()
            if self._converted:
                await self.output_queue.put(
                    CTFConversionResult(self._converted, dict(self._thread_name))
                )

    def _flush_remaining(self) -> list[dict]:
        """Flush any remaining unprocessed messages in the batch."""
        if not self._batch:
            return []
        result = self._parse_batch(self._batch)
        self._batch.clear()
        return result

    def _parse_batch(self, msgs: list) -> list[dict]:
        out = []
        for msg in msgs:
            # A slightly faster hasattr, the error does not signify any actual failure
            try:
                _ = msg.event
            except AttributeError:
                continue

            if not self.checked_timebase:
                assert msg.default_clock_snapshot.clock_class.frequency == 1e9
                self.checked_timebase = True

            ev = _parse_msg(
                msg,
                self._thread_name,
                self._current_thread,
                self._custom_metadata,
                self._custom_event_begin,
                self._custom_event_end,
                self._custom_event_name_func,
                self._custom_event_args_func,
                self._skip_args,
            )

            if ev is not None:
                out.append(ev)

        return out


def stream_ctf_to_tef(
    q: asyncio.Queue,
    skip_args: bool = False,
    custom_metadata: dict[str, CustomMetadataDefinition] | None = None,
    custom_events: list[CustomEventDefinition] | None = None,
    batch_size: int = 50,
    flush_interval_s: float = 0.01,
) -> StreamingCTFToTEF:
    """
    Creates a streaming CTF-to-TEF converter backed by a background task.

    Parameters
    ----------
    q : asyncio.Queue
        Incoming message queue.
    skip_args : bool
        Whether the arguments of events should be ignored.
    custom_metadata : dict[str, CustomMetadataDefinition] | None
        Dictionary mapping CTF event to the TEF metadata.
    custom_events : list[CustomEventDefinition] | None
        List with mapping of the beginning and the end represented by CTF events
        to a new TEF event.
    batch_size : int
        Number of messages to accumulate before flushing.
    flush_interval_s : float
        Maximum time (seconds) to wait before flushing regardless of batch size.

    Returns
    -------
    StreamingCTFToTEF
        Instance with an ``output_queue`` attribute yielding CTFConversionResult objects.
        Call ``.start()`` to begin the background task, and ``.stop()`` to cancel it.
    """
    converter = StreamingCTFToTEF(
        q,
        skip_args=skip_args,
        custom_metadata=custom_metadata,
        custom_events=custom_events,
        batch_size=batch_size,
        flush_interval_s=flush_interval_s,
    )
    return converter


def ctf_to_tef(
    path: str,
    skip_args: bool = False,
    custom_metadata: dict[str, CustomMetadataDefinition] | None = None,
    custom_events: list[CustomEventDefinition] | None = None,
) -> CTFConversionResult:
    """
    Converts CTF trace to the JSON in TEF format.

    Parameters
    ----------
    path : str
        Path to the file with trace in CTF.
    skip_args : bool
        Whether the arguments of events should be ignored.
    custom_metadata : dict[str, CustomMetadataDefinition] | None
        Dictionary mapping CTF event to the TEF metadata.
    custom_events : list[CustomEventDefinition] | None
        List with mapping of the beginning and the end represented by CTF events
        to a new TEF event.

    Returns
    -------
    CTFConversionResult
        The converted trace and information about thread names
    """
    if custom_metadata is None:
        custom_metadata = {}
    if custom_events is None:
        custom_events = []

    # Prepare custom events mapping
    custom_event_begin = defaultdict(list)
    custom_event_end = defaultdict(list)
    custom_event_name_func = {}
    custom_event_args_func = {}
    for event_def in custom_events:
        custom_event_begin[event_def.enter_event_name].append(event_def.new_name)
        custom_event_end[event_def.exit_event_name].append(event_def.new_name)
        custom_event_name_func[event_def.enter_event_name] = event_def.suffix_func
        custom_event_name_func[event_def.exit_event_name] = event_def.suffix_func
        custom_event_args_func[event_def.enter_event_name] = event_def.additional_arg_func
        custom_event_args_func[event_def.exit_event_name] = event_def.additional_arg_func

    converted = []

    thread_name = {}
    current_thread = defaultdict(int)
    msg_it = bt2.TraceCollectionMessageIterator(path)
    # Try to get main thread ID
    while True:
        try:
            msg = next(msg_it)
        except StopIteration:
            break
        except bt2._Error:
            break

        try:
            ev = msg.event
        except AttributeError:
            continue
        fields = ev.payload_field
        if not ev.name.startswith("thread_") or fields.get("name", None) != "main":
            continue
        thread_name["main"] = int(fields.get("thread_id", 0))
        current_thread[fields["cpu_id"]] = thread_name["main"]
        break
    # Restart the iterator
    msg_it = bt2.TraceCollectionMessageIterator(path)
    while True:
        try:
            msg = next(msg_it)
        except StopIteration:
            break
        except bt2._Error:
            break

        try:
            ev = msg.event
        except AttributeError:
            continue
        parsed = _parse_msg(
            msg,
            thread_name,
            current_thread,
            custom_metadata,
            custom_event_begin,
            custom_event_end,
            custom_event_name_func,
            custom_event_args_func,
            skip_args,
        )
        if parsed is not None:
            converted.append(parsed)

    return CTFConversionResult(converted, thread_name)


ZEPHYR_METADATA_RELPATH = Path("subsys") / "tracing" / "ctf" / "tsdl" / "metadata"


def deduce_zephyr_base() -> Path:
    """
    Resolves the ZEPHYR_BASE path.

    Returns
    -------
    Path
        ZEPHYR_BASE path

    Raises
    ------
    FileNotFoundError
        When no candidate points at a Zephyr repository.
    """
    checked = []

    if zephyr_base := os.environ.get("ZEPHYR_BASE"):
        base = Path(zephyr_base)
        if (base / ZEPHYR_METADATA_RELPATH).exists():
            return base
        print(
            f"ZEPHYR_BASE ({base}) is not a Zephyr repository:"
            f" {ZEPHYR_METADATA_RELPATH} is missing, falling back to workspace lookup",
            file=sys.stderr,
        )
        checked.append(f"{base} (ZEPHYR_BASE)")

    module_root = Path(__file__).resolve().parents[1]
    for workspace in (module_root.parent, module_root.parents[1]):
        base = workspace / "zephyr"
        if (base / ZEPHYR_METADATA_RELPATH).exists():
            return base
        checked.append(str(base))

    raise FileNotFoundError(
        "Cannot locate a Zephyr repository. Set ZEPHYR_BASE or pass --zephyr-base."
        f" Checked: {', '.join(checked)}"
    )


def instrumentation_ctf_to_tef(
    path: str,
    instrumentation_elf: Path,
    zephyr_base: str | None = None,
) -> CTFConversionResult:
    """
    Converts CTF instrumentation trace to the JSON in TEF format.

    Parameters
    ----------
    path : str
        Path to the file with trace in CTF.
    zephyr_base : str
        The path to a Zephyr repository.
    instrumentation_elf : Path
        Path to the Zephyr elf file.

    Returns
    -------
    CTFConversionResult
        The converted trace and information about thread names
    """
    zephyr_base = zephyr_base if zephyr_base else deduce_zephyr_base()
    assert zephyr_base is not None and zephyr_base.exists(), (
        f"Missing or invalid path to Zephyr repository: {zephyr_base}"
    )
    sys.path.insert(1, f"{zephyr_base}/scripts/instrumentation")
    import zaru

    converted, _ = zaru.get_traces_in_trace_event_format(path, instrumentation_elf, True)
    return CTFConversionResult(converted, None)


def merge_metadata(dst_dir: Path, zephyr_base: Path | None = None) -> Path:
    """
    Write the merged Zephyr + Zephelin CTF metadata into provided directory.

    Parameters
    ----------
    dst_dir : Path
        Directory the merged metadata file is written into.
    zephyr_base : Path | None
        Path to the Zephyr repository.

    Returns
    -------
    Path
        Path to the metadata file.

    Raises
    ------
    FileNotFoundError
        When either the Zephyr base or Zephelin metadata cannot be found.
    """
    zephyr_base = zephyr_base if zephyr_base else deduce_zephyr_base()
    zephyr_metadata = zephyr_base / ZEPHYR_METADATA_RELPATH
    if not zephyr_metadata.exists():
        raise FileNotFoundError(f"Zephyr CTF metadata ({zephyr_metadata}) does not exist")

    zpl_metadata = Path(__file__).parents[1] / "zpl" / "metadata"
    if not zpl_metadata.exists():
        raise FileNotFoundError(f"Zephelin metadata ({zpl_metadata}) does not exist")

    dst_metadata = dst_dir / "metadata"
    dst_metadata.write_text(zephyr_metadata.read_text() + zpl_metadata.read_text())
    return dst_metadata


@contextmanager
def prepare_dir(trace: Path, zephyr_base: Path | None = None):
    """
    Prepare temporary directory with CTF and extended metadata.

    Yields
    ------
    Path
        The temporary directory with CTF and custom metadata.
    """
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        tmp_dir = Path(tmp_dir)

        tmp_ctf = tmp_dir / trace.name
        with open(trace, "rb") as trace_in_f, open(tmp_ctf, "wb") as trace_out_f:
            # iterate over packets to remove last, partially written packet
            while True:
                stream_id = trace_in_f.read(2)
                packet_size = trace_in_f.read(2)
                packet_size_bytes = int.from_bytes(packet_size, "little", signed=False) // 8
                if packet_size_bytes <= 4:
                    break

                packet = trace_in_f.read(packet_size_bytes - 4)

                if len(packet) != packet_size_bytes - 4:
                    # partially written packet detected
                    break

                trace_out_f.write(stream_id)
                trace_out_f.write(packet_size)
                trace_out_f.write(packet)

        try:
            merge_metadata(tmp_dir, zephyr_base)
        except FileNotFoundError as e:
            print(str(e), file=sys.stderr)
            exit(1)

        yield tmp_dir


@contextmanager
def prepare_dir_for_instrumentation(trace: Path, instrumentation_metadata: Path):
    """
    Prepare temporary directory with CTF and extended metadata for instrumentation traces.

    Yields
    ------
    Path
        The temporary directory with CTF and custom metadata.
    """
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        tmp_dir = Path(tmp_dir)

        tmp_ctf = tmp_dir / trace.name
        copy2(trace, tmp_ctf)

        tmp_metadata = tmp_dir / "metadata"
        copy2(instrumentation_metadata, tmp_metadata)

        yield tmp_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "ctf2tef",
        description=__doc__,
        allow_abbrev=False,
    )
    parser.add_argument(
        "ctf_trace",
        type=Path,
        help="The path to a trace in CTF format",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="The path where converted trace will be saved, "
        "if not provided trace will be printed to STDOUT",
    )
    parser.add_argument(
        "--zephyr-base",
        type=Path,
        default=os.environ.get("ZEPHYR_BASE", None),
        help="The path to a Zephyr repository, can be passed with $ZEPHYR_BASE, "
        "otherwise will be deduced based on the script path",
    )
    parser.add_argument(
        "--exclude-args",
        action="store_true",
        help="Whether event arguments should be skipped",
    )
    parser.add_argument(
        "--instrumentation-traces",
        action="store_true",
        help="Whether the CTF file contains instrumentation traces",
    )
    parser.add_argument(
        "--instrumentation-metadata",
        help="The generated instrumentation metadata file",
        type=Path,
        required=False,
        default=Path(__file__).parent.parent / "build" / "ctf_metadata",
    )
    parser.add_argument(
        "--instrumentation-elf",
        help="Elf file for instrumentation traces",
        type=Path,
        required=False,
        default=Path(__file__).parent.parent / "build" / "zephyr" / "zephyr.elf",
    )
    args = parser.parse_args(sys.argv[1:])

    if not args.ctf_trace.exists():
        print(f"Specified trace ({args.ctf_trace}) does not exist", file=sys.stderr)
        exit(1)

    if args.instrumentation_traces:
        with prepare_dir_for_instrumentation(
            args.ctf_trace, args.instrumentation_metadata
        ) as tmp_dir:
            converted = instrumentation_ctf_to_tef(
                str(tmp_dir), args.instrumentation_elf, args.zephyr_base
            ).tef
    else:
        with prepare_dir(args.ctf_trace, args.zephyr_base) as tmp_dir:
            converted = ctf_to_tef(str(tmp_dir), args.exclude_args).tef

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w") as fd:
            json.dump(converted, fd)
    else:
        print(json.dumps(converted, indent=2))
