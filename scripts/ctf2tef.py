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
import collections
import json
import os
import sys
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from math import isnan
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory
from typing import Any, AsyncGenerator, Callable, NamedTuple

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
    msg: bt2._EventMessageConst,
    name: str,
    tid: int,
    phase: EventPhase,
    shift: float = 0,
    skip_args: bool = False,
    additional_args: dict | None = None,
):
    """
    Prints the event in TEF format.

    Parameters
    ----------
    msg : bt2._EventMessageConst
        Representation of the event message to be printed.
    name : str
        The name of event.
    tid : int
        The thread ID.
    phase : EventPhase
        The event phase, usually either begin or end.
    shift : float
        The shift added to a timestamp.
    skip_args : bool
        Whether arguments should be skipped.
    additional_args : dict | None
        Additional data appended to "args".
    """
    if name == "named_event":
        name = str(msg.event.payload_field.get("name", name))
    return {
        "name": name,
        "cat": "zephyr",
        "ph": phase.value,
        "ts": extract_us(msg) + shift,
        "pid": 0,
        "tid": tid,
    } | (
        {
            "args": {
                **convert_from_bt2(msg.event.payload_field),
                **(additional_args if additional_args else {}),
            }
        }
        if not skip_args and msg.event.payload_field
        else {}
    )


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
    fields = msg.event.payload_field if msg.event.payload_field else {}
    thread_id = int(
        fields.get("thread_id", current_thread[msg.event.payload_field.get("cpu_id", -1)])
    )
    # Process custom metadata
    if msg.event.name in custom_metadata:
        m = custom_metadata[msg.event.name]
        return emit_event(
            msg,
            f"{m.new_name}{m.suffix_func(msg) if m.suffix_func else ''}",
            thread_id,
            EventPhase.METADATA,
            skip_args=skip_args,
            additional_args=m.additional_arg_func(msg) if m.additional_arg_func else {},
        )
    # Process custom events
    if msg.event.name in custom_event_begin:
        return emit_event(
            msg,
            f"{custom_event_begin[msg.event.name][0]}{custom_event_name_func[msg.event.name](msg)}",
            thread_id,
            EventPhase.BEGIN,
            skip_args=skip_args,
            additional_args=custom_event_args_func[msg.event.name](msg)
            if custom_event_args_func[msg.event.name]
            else None,
        )
    if msg.event.name in custom_event_end:
        return emit_event(
            msg,
            f"{custom_event_end[msg.event.name][0]}{custom_event_name_func[msg.event.name](msg)}",
            thread_id,
            EventPhase.END,
            skip_args=skip_args,
            additional_args=custom_event_args_func[msg.event.name](msg)
            if custom_event_args_func[msg.event.name]
            else None,
        )
    # Process Zephyr events (starts with *_enter and finishes with *_exit)
    if msg.event.name.endswith("_enter"):
        return emit_event(
            msg,
            msg.event.name[:-6],
            thread_id,
            EventPhase.BEGIN,
            skip_args=skip_args,
        )
    if msg.event.name.endswith("_exit"):
        return emit_event(
            msg,
            msg.event.name[:-5],
            thread_id,
            EventPhase.END,
            skip_args=skip_args,
        )
    # Check whether thread has changed
    if str(msg.event.name).startswith("thread_") and "thread_id" in fields:
        thread_name[str(fields["name"])] = int(fields["thread_id"])
    # Check whether thread has changed
    if msg.event.name == "thread_switched_in":
        current_thread[msg.event.payload_field["cpu_id"]] = thread_id = int(fields["thread_id"])


async def stream_ctf_to_tef(
    q,
    skip_args: bool = False,
    custom_metadata: dict[str, CustomMetadataDefinition] | None = None,
    custom_events: list[CustomEventDefinition] | None = None,
) -> AsyncGenerator[CTFConversionResult, Any]:
    """
    Converts CTF trace to the JSON in TEF format.

    Parameters
    ----------
    q: asyncio.Queue
        Incoming message queue
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

    while True:
        if len(converted):
            yield CTFConversionResult(converted, thread_name)
            converted = []
        msg = await q.get()
        # Skip messages without events
        if not hasattr(msg, "event"):
            continue
        event = _parse_msg(
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
        if event is not None:
            converted.append(event)


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

        if not hasattr(msg, "event"):
            continue
        fields = msg.event.payload_field
        if not msg.event.name.startswith("thread_") or fields.get("name", None) != "main":
            continue
        thread_name["main"] = int(fields.get("thread_id", 0))
        current_thread[msg.event.payload_field["cpu_id"]] = thread_name["main"]
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

        # Skip messages without events
        if not hasattr(msg, "event"):
            continue
        event = _parse_msg(
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
        if event is not None:
            converted.append(event)

    return CTFConversionResult(converted, thread_name)


def deduce_zephyr_base():
    """
    Deduces ZEPHYR_BASE path.

    Returns
    -------
    Path
        ZEPHYR_BASE path
    """
    return Path(__file__).parents[2] / "zephyr"


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
    zephyr_metadata = zephyr_base / "subsys" / "tracing" / "ctf" / "tsdl" / "metadata"
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
