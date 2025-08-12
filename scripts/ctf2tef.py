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
from typing import Any, Callable, NamedTuple

import bt2  # From the babeltrace2 package.

# Currently neither Speedscope nor Perfetto support
# instantaneous event, therefore a small "quant" of time is used
# to represent event length.
# Later on, a separate visualization feature can be added for such events.
INSTANT_EVENT_LENGTH = 1.0
# The first timestamp of the trace
BASE_TIME = None


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
    global BASE_TIME
    ns = msg.default_clock_snapshot.value
    if BASE_TIME is None:
        BASE_TIME = ns
    return (ns - BASE_TIME) * 1e-3


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
    custom_metadata : list[CustomMetadataDefinition] | None
        Dictionary mapping CTF event to the TEF metadata.
    custom_events : dict[str, CustomEventDefinition] | None
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
    current_thread = 0  # By default use 0 as main thread ID
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
        current_thread = thread_name["main"]
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
        fields = msg.event.payload_field if msg.event.payload_field else {}
        thread_id = int(fields.get("thread_id", current_thread))
        # Process custom metadata
        if msg.event.name in custom_metadata:
            m = custom_metadata[msg.event.name]
            converted.append(
                emit_event(
                    msg,
                    f"{m.new_name}{m.suffix_func(msg) if m.suffix_func else ''}",
                    thread_id,
                    EventPhase.METADATA,
                    skip_args=skip_args,
                    additional_args=m.additional_arg_func(msg) if m.additional_arg_func else {},
                )
            )
            continue
        # Process custom events
        if msg.event.name in custom_event_begin:
            converted.append(
                emit_event(
                    msg,
                    f"{custom_event_begin[msg.event.name][0]}{custom_event_name_func[msg.event.name](msg)}",
                    thread_id,
                    EventPhase.BEGIN,
                    skip_args=skip_args,
                    additional_args=custom_event_args_func[msg.event.name](msg)
                    if custom_event_args_func[msg.event.name]
                    else None,
                )
            )
            continue
        if msg.event.name in custom_event_end:
            converted.append(
                emit_event(
                    msg,
                    f"{custom_event_end[msg.event.name][0]}{custom_event_name_func[msg.event.name](msg)}",
                    thread_id,
                    EventPhase.END,
                    skip_args=skip_args,
                    additional_args=custom_event_args_func[msg.event.name](msg)
                    if custom_event_args_func[msg.event.name]
                    else None,
                )
            )
            continue
        # Process Zephyr events (starts with *_enter and finishes with *_exit)
        if msg.event.name.endswith("_enter"):
            converted.append(
                emit_event(
                    msg,
                    msg.event.name[:-6],
                    thread_id,
                    EventPhase.BEGIN,
                    skip_args=skip_args,
                )
            )
            continue
        if msg.event.name.endswith("_exit"):
            converted.append(
                emit_event(
                    msg,
                    msg.event.name[:-5],
                    thread_id,
                    EventPhase.END,
                    skip_args=skip_args,
                )
            )
            continue
        # Check whether thread has changed
        if str(msg.event.name).startswith("thread_"):
            thread_name[str(fields["name"])] = int(fields["thread_id"])
        # Check whether thread has changed
        if msg.event.name == "thread_switched_in":
            current_thread = thread_id = int(fields["thread_id"])
        # Add instantaneous event representation
        converted += [
            emit_event(msg, msg.event.name, thread_id, EventPhase.BEGIN, skip_args=skip_args),
            emit_event(
                msg, msg.event.name, thread_id, EventPhase.END, INSTANT_EVENT_LENGTH, skip_args
            ),
        ]
    return CTFConversionResult(converted, thread_name)


@contextmanager
def prepare_dir(trace: Path, zephyr_base: Path | None = None):
    """
    Prepare temporary directory with CTF and extended metadata.

    Yields
    ------
    Path
        The temporary directory with CTF and custom metadata.
    """
    with TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)

        tmp_ctf = tmp_dir / trace.name
        copy2(trace, tmp_ctf)

        base = Path(__file__).parent.parent
        zephyr_base = zephyr_base if zephyr_base else base.parent / "zephyr"
        zephyr_metadata = zephyr_base / "subsys" / "tracing" / "ctf" / "tsdl" / "metadata"
        if not zephyr_metadata.exists():
            print(
                f"Zephyr CTF metadata ({zephyr_metadata}) does not exist",
                file=sys.stderr,
            )
            exit(1)

        tmp_metadata = tmp_dir / zephyr_metadata.name
        copy2(zephyr_metadata, tmp_metadata)

        zpl_metadata = base / "zpl" / "metadata"
        if not zpl_metadata.exists():
            print(f"Zeppelin metadata ({zpl_metadata}) does not exist", file=sys.stderr)
            exit(1)

        with zpl_metadata.open("r") as fd:
            zpl_meta_raw = fd.read()
        with tmp_metadata.open("a") as fd:
            fd.write(zpl_meta_raw)

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
    args = parser.parse_args(sys.argv[1:])

    if not args.ctf_trace.exists():
        print(f"Specified trace ({args.ctf_trace}) does not exist", file=sys.stderr)
        exit(1)

    with prepare_dir(args.ctf_trace, args.zephyr_base) as tmp_dir:
        converted = ctf_to_tef(str(tmp_dir), args.exclude_args).tef

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w") as fd:
            json.dump(converted, fd)
    else:
        print(json.dumps(converted, indent=2))
