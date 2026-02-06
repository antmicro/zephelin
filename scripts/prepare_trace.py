# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Script preparing trace (in TEF) based on the CTF trace and metadata, e.g. TFLM model.
"""

import argparse
import functools
import json
import os
import re
import subprocess
import sys
from collections import defaultdict, namedtuple
from pathlib import Path
from typing import Callable

import bt2
from ctf2tef import (
    CustomEventDefinition,
    CustomMetadataDefinition,
    EventPhase,
    ctf_to_tef,
    prepare_dir,
)
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from extract_tvm_model_data import (
    DEFAULT_OP_PREFIX_RE,
    DEFAULT_OP_SUFFIX_RE,
    argparse_regex,
)

# Name of TEF Model event
MODEL_EVENT_NAME = "MODEL"
# Name of TEF Inference event
INFERENCE_EVENT_NAME = "INFERENCE::MODEL"
# Key of the argument used to store tvmgen functions prefix
TVMGEN_PREFIX_ARG = "_tvmgen_prefix"
# Whether TVM event were detected in a trace
TVM_EVENTS = False
# Mapping of models IDs to consecustive numbers
MODEL_IDS_MAPPING = {}
# Prefix for instrumentation events
INSTR_EVENT_PREFIX = "instr::"
# Prefix for scheduling events
INSTR_SCHED_PREFIX = "instr_sched_switch"

CPPFILT_CMD = [os.environ.get("ZPL_DEMANGLE_CMD", "c++filt")]


# The list of custom events definitions
def create_custom_events(
    tvm_op_remove_prefix: re.Pattern = DEFAULT_OP_PREFIX_RE,
    tvm_op_remove_suffix: re.Pattern = DEFAULT_OP_SUFFIX_RE,
    multi_model_trace: bool = False,
    symbol_map: dict[int, list[str]] | None = None,
) -> list[CustomEventDefinition]:
    """
    Creates custom events.

    Parameters
    ----------
    tvm_op_remove_prefix : re.Pattern
        Pattern removing TVM operator prefix.
    tvm_op_remove_suffix : re.Pattern
        Pattern removing TVM operator type suffix.
    multi_model_trace : bool
        Whether the trace contains more than one model.
    symbol_map : dict[int, list[str]] | None
        Dict mapping addresses to mangled symbols.

    Returns
    -------
    list[CustomEventDefinition]
        Created events.
    """
    if symbol_map is None:
        symbol_map = {}
    # The mapping of thread ID to model ID
    ACTIVE_INFERENCES = {}
    # The mapping of currently processed TVM events, grouped by thread ID
    CURRENT_TVM_INFERENCE = {}

    def tflm_op_name(msg: "bt2._EventMessageConst") -> str:
        fields = msg.event.payload_field
        if not fields:
            return ""
        name = str(fields.get("tag", ""))

        # Add subgraph index at the end, if exists
        if "subgraph_idx" in fields:
            name += f"_{fields['subgraph_idx']}"

        # Add operator index at the end, if exists
        if "op_idx" in fields:
            name += f"_{fields['op_idx']}"

        model_num = ""
        if multi_model_trace:
            thread_id = fields.get("thread_id", None)
            model_num = ACTIVE_INFERENCES.get(thread_id, "") if thread_id else ""

        return f"{model_num}::{name}"

    def tvm_op_name(msg: "bt2._EventMessageConst") -> str:
        """
        Generates suffix for model event name.
        """
        nonlocal CURRENT_TVM_INFERENCE
        global TVM_EVENTS

        TVM_EVENTS = True
        fields = msg.event.payload_field
        if not fields:
            return ""
        name = str(fields.get("tag", ""))
        if msg.event.name.endswith("_enter"):
            thread_id = int(str(fields.get("thread_id", None)))
            if thread_id not in CURRENT_TVM_INFERENCE:
                CURRENT_TVM_INFERENCE[thread_id] = []
            CURRENT_TVM_INFERENCE[thread_id].append(name)
        name = tvm_op_remove_prefix.sub("", name)

        return name

    def modify_op_type_name(
        args: dict,
        *patterns: re.Pattern,
    ) -> Callable[["bt2._EventMessageConst"], dict]:
        def arg_func(msg: "bt2._EventMessageConst"):
            fields = msg.event.payload_field or {}
            tag = str(fields.get("tag", ""))
            if not tag:
                return args

            for pattern in patterns:
                tag = pattern.sub("", tag)
            return args | {"tag": tag}

        return arg_func

    def inference_model_number(msg: bt2._EventMessageConst) -> str:
        """
        Generates suffix for inference event.
        """
        fields = msg.event.payload_field
        if not fields:
            return ""
        model_id = int(fields.get("model_id", None))
        if model_id not in MODEL_IDS_MAPPING:
            MODEL_IDS_MAPPING[model_id] = len(MODEL_IDS_MAPPING)
        start = msg.event.name.endswith("_enter")
        thread_id = fields.get("thread_id", None)
        if thread_id and start:
            ACTIVE_INFERENCES[thread_id] = MODEL_IDS_MAPPING[model_id]
        elif thread_id:
            ACTIVE_INFERENCES[thread_id] = None
        return str(MODEL_IDS_MAPPING[model_id])

    def inference_additional_args(msg: bt2._EventMessageConst) -> dict:
        nonlocal CURRENT_TVM_INFERENCE

        fields = msg.event.payload_field
        if not fields:
            return {}
        thread_id = int(fields.get("thread_id", None))
        if msg.event.name.endswith("_enter"):
            return {}
        if func_names := CURRENT_TVM_INFERENCE.get(thread_id, []):
            from extract_tvm_model_data import get_common_prefix

            common_prefix = get_common_prefix(func_names)
            CURRENT_TVM_INFERENCE[thread_id] = []
            if common_prefix:
                return {TVMGEN_PREFIX_ARG: common_prefix}
        return {}

    @functools.lru_cache(maxsize=1024)
    def demangle(func: str):
        cmd = CPPFILT_CMD + [func]
        try:
            func_demangled = subprocess.check_output(cmd, text=True).strip()
        except subprocess.CalledProcessError as e:
            print(f"Error message: {e}")
            func_demangled = func
        return func_demangled

    def instr_event_suffix(msg: bt2._EventMessageConst) -> str:
        callee = str(msg.event.payload_field.get("callee", ""))

        if callee.strip().lstrip("+-").isdigit():
            symbol_map_key = int(callee)
        else:
            symbol_map_key = 0

        symbol_list = symbol_map.get(symbol_map_key)

        if symbol_list:
            return demangle(symbol_list[0])
        else:
            print(f"No symbols found - using callee address {hex(symbol_map_key)}")
            return hex(symbol_map_key)

    return [
        CustomEventDefinition(
            MODEL_EVENT_NAME,
            "zpl_tflm_enter",
            "zpl_tflm_exit",
            tflm_op_name,
            lambda _: {"runtime": "TFLite Micro"},
        ),
        CustomEventDefinition(
            f"{MODEL_EVENT_NAME}::",
            "zpl_tvm_enter",
            "zpl_tvm_exit",
            tvm_op_name,
            modify_op_type_name(
                {"runtime": "microTVM"},
                tvm_op_remove_prefix,
                tvm_op_remove_suffix,
            ),
        ),
        CustomEventDefinition(
            "SCOPE::",
            "zpl_scope_enter",
            "zpl_scope_exit",
            lambda msg: msg.event.payload_field.get("scope_name", ""),
            None,
        ),
        CustomEventDefinition(
            INFERENCE_EVENT_NAME,
            "zpl_inference_enter",
            "zpl_inference_exit",
            inference_model_number if multi_model_trace else lambda _: "",
            inference_additional_args,
        ),
        CustomEventDefinition(
            INSTR_EVENT_PREFIX,
            "func_with_context_enter",
            "func_with_context_exit",
            instr_event_suffix,
            None,
        ),
        CustomEventDefinition(
            INSTR_SCHED_PREFIX,
            "sched_switched_in",
            "sched_switched_out",
            lambda msg: msg.event.payload_field.get("thread_name", ""),
            None,
        ),
    ]


# Mapping of memory regions initial addresses to their sizes in bytes,
# used for extracting region symbols from built Zephyr ELF
# and calculating total size of the RAM.
REGION_SIZES = {}


def memory_data(msg) -> dict:
    """
    Returns additional arguments with memory ragion name.
    """
    if not (args := msg.event.payload_field):
        return {}
    if "memory_addr" in args:
        addr = int(args["memory_addr"])
        REGION_SIZES[addr] = max(REGION_SIZES.get(addr, 0), int(args["used"] + args["unused"]))
    try:
        # Get enum label and remove zpl_ prefix
        # This will override "memory_region"
        return {"memory_region": args["memory_region"].labels[0][4:]}
    except Exception:
        return {}


# The dictionary of custom metadata events, where the key is CTF event name
# and value is a definition of new metadata event.
CUSTOM_METADATA = {
    "zpl_memory": CustomMetadataDefinition("MEMORY", None, memory_data),
    "zpl_cpu_load_event": CustomMetadataDefinition("CPU_LOAD", None, None),
    "zpl_die_temp_event": CustomMetadataDefinition("DIE_TEMP", None, None),
    "thread_info": CustomMetadataDefinition("THREAD", None, None),
}


def add_model_metadata(trace: list, data: dict):
    """
    Adds model metadata to the trace.
    """
    trace.insert(
        0,
        {
            "name": "MODEL",
            "cat": "zephyr",
            "ph": EventPhase.METADATA.value,
            "pid": 0,
            "tid": 0,
            "ts": 0,
            "args": data,
        },
    )


def extract_symbol_map(zephyr_elf_path: Path) -> dict[int, list[str]]:
    """
    Extracts memory symbols from the provided Zephyr ELF.

    It parses the ELF file to get all available symbols
    and filters out ones that have not appeared in trace.
    """
    if not zephyr_elf_path.exists():
        print(
            f"Zephyr ELF ({zephyr_elf_path}) does not exist, memory symbols will not be extracted",
            file=sys.stderr,
        )
        return

    addr_to_symbol = defaultdict(list)

    try:
        with open(zephyr_elf_path, "rb") as f:
            elffile = ELFFile(f)

            for section in elffile.iter_sections():
                if isinstance(section, SymbolTableSection):
                    for symbol in section.iter_symbols():
                        if (
                            symbol["st_shndx"] != "SHN_UNDEF"
                            and symbol.name
                            and not symbol.name.startswith("$")
                        ):
                            addr_hex = f"{symbol['st_value']:08x}"
                            addr_to_symbol[addr_hex].append(symbol.name)

    except Exception as e:
        print(f"Symbol extraction failed: {e}", file=sys.stderr)
        return

    return addr_to_symbol


def extract_memory_symbols(addr_to_symbol: dict[int, list[str]]) -> dict[int, list[str]]:
    """
    Extracts memory symbols from the provided Zephyr ELF.

    It uses `nm` from GNU binutils to get all available symbols
    and filters out ones that have not appeared in trace.
    """
    mem_symbols = {}
    for addr in REGION_SIZES:
        if addr not in addr_to_symbol or not addr_to_symbol[addr]:
            print(f"Cannot find symbol for address 0x{addr:x}", file=sys.stderr)
            continue
        # Choose last found symbol
        mem_symbols[addr] = addr_to_symbol[addr][-1]

    return mem_symbols


def zaru_format(instr_trace: list[dict]) -> list[dict]:
    """
    Adjusts format of trace in a similar manner as in zaru.py script.
    """
    trace_events = []
    named_thread_list = []

    for event in instr_trace:
        ph = event.get("ph", "")

        if ph not in ["B", "E"]:
            continue

        name = event.get("name", "")

        # When tracing non-application code usually there isn't a thread ID
        # associated to the context, so in this case change thread ID to 0.
        tid = event.get("args", {}).get("thread_id", 0)

        ts = float(event.get("ts", 0.0))
        tn = event.get("args", {}).get("thread_name", "none-thread")

        if tn == "none-thread":
            tid = -1

        if not name:
            print(f"Skipped event at ts = {ts}, with tid = {tid}, tn = {tn} due to empty name")
            continue

        # Check if it's necessary to name a thread/process in the Event
        # Trace Format. Once a new thread is found it's named and included
        # to the list of named threads, threads need to be named only once.
        # Set all process IDs to 0 to match with Zephelin events
        # By default instrumentation subsystem uses thread ID
        # for "tid" (thread ID) and "pid" (process ID)
        if tn not in named_thread_list:
            named_thread_list.append(tn)

            trace_event = {
                "args": {"name": tn},
                "cat": "__metadata",
                "name": "thread_name",
                "ph": "M",
                "pid": 0,
                "tid": tid,
                "ts": 0.0,
            }
            trace_events.append(trace_event)

        trace_event = {"ts": ts, "pid": 0, "tid": tid, "ph": ph, "name": name}
        trace_events.append(trace_event)

    return trace_events


def remove_events_without_beginning(instr_trace: list[dict]) -> list[dict]:
    """
    Remove events' ends that do not have beginnings.
    """
    EventHash = namedtuple("EventHash", ["name", "tid"])

    begins = []
    to_remove = []
    for i, e in enumerate(instr_trace):
        if e["ph"] == "B":
            begins.insert(0, EventHash(e["name"], e["tid"]))
            continue
        if e["ph"] != "E":
            continue
        h = EventHash(e["name"], e["tid"])
        if h not in begins:
            to_remove.append(i)
        else:
            begins.remove(h)
    removed = []
    for i in to_remove[::-1]:
        removed.append(instr_trace[i])
        instr_trace.pop(i)
    if removed:
        print(
            "Removed ends of following events as they do not have beginnings:\n\t"
            + "\n\t".join(f"{e['name']} ({e['ts']:.2f}us)" for e in removed)
        )
    # Find last timestamps per thread
    thread_ids = set((e.tid for e in begins))
    last_ts_per_thread = {}
    for e in instr_trace[::-1]:
        tid = e["tid"]
        if tid not in thread_ids:
            continue
        last_ts_per_thread[tid] = e["ts"]
        thread_ids.remove(tid)
        if not thread_ids:
            break
    # Add event ends
    for be in begins:
        instr_trace.append({
            # Add small value to make sure the event do not end in the same timestamp
            "ts": last_ts_per_thread[be.tid] + 0.1,
            "pid": 0,
            "tid": be.tid,
            "ph": "E",
            "name": be.name,
        })

    return instr_trace


def fix_timestamps(
    instr_trace: list[dict], zpl_trace: list[dict], verbose: bool = False
) -> list[dict]:
    """
    Scan instrumentation events and fix timestamps
    making sure parents do not end before children.
    """

    def matching_events(a, b):
        return a["name"] == b["name"] and a["tid"] == b["tid"]

    adjusted = []
    to_remove = []
    for instr_id, instr_beg_ev in enumerate(instr_trace[:]):
        if instr_beg_ev["ph"] != "B":
            continue
        # Get end instrumentation event
        instr_end_id, instr_end_ev = next(
            filter(
                lambda ie: matching_events(ie[1], instr_beg_ev) and ie[1]["ph"] == "E",
                enumerate(instr_trace[instr_id + 1 :]),
            ),
            (None, None),
        )
        if instr_end_ev is None:
            print(f"Cannot find end of {instr_beg_ev['name']} event")
            continue
        instr_end_id += instr_id + 1
        # Remove events with invalid timestamp
        # Events from the instrumentation should be reported consecutively across threads
        if instr_end_ev["ts"] < instr_beg_ev["ts"]:
            to_remove.extend((instr_end_id, instr_id))
            continue

        ts = instr_beg_ev["ts"]
        while True:
            # Get child event from ZPL traces
            zpl_beg_ev = next(
                filter(
                    lambda e: e["tid"] == instr_beg_ev["tid"]
                    and e["ph"] == "B"
                    and ts <= e["ts"] < instr_end_ev["ts"],
                    zpl_trace,
                ),
                None,
            )
            if zpl_beg_ev is None:
                break
            # Get end event of the child
            zpl_end_ev = next(
                filter(
                    lambda e: matching_events(e, zpl_beg_ev)
                    and e["ph"] == "E"
                    and e["ts"] > zpl_beg_ev["ts"],
                    zpl_trace,
                ),
                None,
            )

            if zpl_end_ev is None:
                break

            if zpl_end_ev and zpl_end_ev["ts"] > instr_end_ev["ts"]:
                # Adjust end of the instrumentation event to not finish before its children
                instr_end_ev["ts"] = zpl_end_ev["ts"]
                adjusted.append(instr_end_ev)
                break
            ts = zpl_end_ev["ts"]

    if to_remove:
        removed = set([instr_trace.pop(i)["name"] for i in sorted(to_remove, reverse=True)])
        if verbose:
            print("Removed events whose ends are before beginnings:\n\t" + "\n\t".join(removed))
    if adjusted and verbose:
        print(
            "Adjusted ends for following instrumentation events, "
            "to avoid collisions with Zephelin events:\n\t"
            + "\n\t".join(f"{e['name']} ({e['ts']}us)" for e in adjusted)
        )

    return instr_trace


def adjust_instrumentation_trace(tef_trace: list[dict]) -> list[dict]:
    """
    Adjusts instrumentation traces to make sure they do not collide with ZPL traces.

    It is achieved with:
    * filtering out scheduling events,
    * splitting traces into instrumentation and ZPL parts,
    * processing trace events in similar manner as `zaru.py` script,
    * removing events without beginnings,
    * closing unfinished events,
    * making events longer to make sure they are not shorter than their children.
    """
    # Filter out scheduling events, as they are dropped in one of zephyr patches
    tef_trace = [ev for ev in tef_trace if not ev.get("name", "").startswith(INSTR_SCHED_PREFIX)]

    # Split the trace into instrumentation and ZPL parts
    instr_trace, zpl_trace = split_instr_zpl(tef_trace)

    instr_trace = zaru_format(instr_trace)

    instr_trace = remove_events_without_beginning(instr_trace)

    instr_trace = fix_timestamps(instr_trace, zpl_trace, verbose=True)

    return zpl_trace + instr_trace


def trim_metadata(tef_trace: list[dict]) -> list[dict]:
    """
    Creates trace with removed metadata events
    that were emitted after the last beginning or end event.
    """
    last_event_ts = max([
        float(e["ts"])
        for e in tef_trace
        if e["ph"] in (EventPhase.BEGIN.value, EventPhase.END.value)
    ])
    return [
        e
        for e in tef_trace
        if e["ph"] != EventPhase.METADATA.value or float(e.get("ts", -1)) <= last_event_ts
    ]


def setup_parser(parser: argparse.ArgumentParser):
    """
    Sets up parser for prepare trace script.
    """
    parser.add_argument(
        "ctf_trace",
        type=Path,
        help="The path to a trace in CTF format",
        default=None,
        nargs="?",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="The path to the output, if not provided, the results will be printed to STDOUT",
        required=True,
    )
    parser.add_argument(
        "--zephyr-base",
        type=Path,
        default=os.environ.get("ZEPHYR_BASE", None),
        help="The path to a Zephyr repository, can be passed with $ZEPHYR_BASE, "
        "otherwise will be deduced based on the script path",
    )
    parser.add_argument(
        "--tflm-model-paths",
        type=Path,
        nargs="+",
        help="Paths to TFLM models, extracted information will be appedened "
        "to the final trace as a metadata",
    )
    parser.add_argument(
        "--tflm-model-ids",
        type=str,
        nargs="+",
        help="IDs of TFLM models in HEX format (0x[0-9a-zA-Z]+) in the same order "
        "as --tflm-model-paths, Model IDs are printed right before the inference",
    )
    parser.add_argument(
        "--tvm-model-paths",
        type=Path,
        nargs="+",
        help="Path to the TVM graph file, extracted information will be appedened "
        "to the final trace as a metadata",
    )
    parser.add_argument(
        "--tvm-model-metadata-paths",
        type=Path,
        nargs="+",
        help="Path to the TVM metadata file, extracted information will be appedened "
        "to the final trace as a metadata",
    )
    parser.add_argument(
        "--tvm-model-op-remove-prefix",
        type=argparse_regex,
        help="Pattern removing TVM operator prefix",
        default=DEFAULT_OP_PREFIX_RE,
    )
    parser.add_argument(
        "--tvm-model-op-remove-suffix",
        type=argparse_regex,
        help="Pattern removing TVM operator type suffix",
        default=DEFAULT_OP_SUFFIX_RE,
    )
    parser.add_argument(
        "--build-dir",
        type=Path,
        help="Path to the build directory",
    )
    parser.add_argument(
        "--zephyr-elf-path",
        type=Path,
        help="Path to the built Zephyr ELF, required for extracting symbols of memory regions",
    )
    parser.add_argument(
        "-i",
        "--instrumentation",
        help="The path to a trace received from instrumentation",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--trim-metadata",
        action="store_true",
        help="Discards all metadata that were emitted after the last trace event",
    )
    return parser


def process_ram_report(ram: dict) -> float:
    """
    Calculates the allocated memory from ram_report without heaps, stack and slabs from metadata.

    Parameters
    ----------
    ram : dict
        The JSON representation of ram_report results (from ram.json file)

    Returns
    -------
    float
        Allocated memory
    """
    if "children" in ram:
        s = 0
        for child in ram["children"]:
            s += process_ram_report(child)
        ram["size"] -= s
        return s

    if (
        "address" not in ram
        or ram["address"] not in REGION_SIZES
        # Exclude z_malloc_heap as its size is based on unused RAM
        or ram["name"] == "z_malloc_heap"
    ):
        return 0

    s = REGION_SIZES[ram["address"]]
    ram["size"] -= s
    return s


def split_instr_zpl(tef_trace: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Split TEF trace into instrumentation and ZPL parts.
    """
    instr_trace = []
    zpl_trace = []
    for ev in tef_trace:
        if ev.get("name", "").startswith(INSTR_EVENT_PREFIX):
            instr_trace.append(ev)
        else:
            zpl_trace.append(ev)

    return instr_trace, zpl_trace


def prepare(args: argparse.Namespace):
    """
    Prepares CTF trace to be visualized.

    This includes converting it to TEF and extending with additional
    metadata with info about memory or used model.
    """
    if not args.build_dir:
        args.build_dir = Path(".") / "build"

    tef_trace, thread_name = [], {}
    if args.zephyr_elf_path is None:
        args.zephyr_elf_path = Path(".") / "build" / "zephyr" / "zephyr.elf"

    multiple_models = False

    if args.ctf_trace is None and args.instrumentation is None:
        raise argparse.ArgumentError(None, "Please provide at least one trace file")

    symbol_map = extract_symbol_map(args.zephyr_elf_path)

    # Convert CTF
    if args.ctf_trace:
        with prepare_dir(args.ctf_trace, args.zephyr_base) as tmp_dir:
            # Detect whether more than one model is used in the trace
            model_ids = set()
            msg_it = bt2.TraceCollectionMessageIterator(str(tmp_dir))
            for msg in msg_it:
                if not hasattr(msg, "event"):
                    continue
                name = str(msg.event.name)
                if name != "zpl_inference_enter":
                    continue
                fields = msg.event.payload_field
                model_id = int(fields.get("model_id", None))
                if model_id and model_id not in model_ids:
                    model_ids.add(model_id)
                    if len(model_ids) >= 2:
                        break
            multiple_models = len(model_ids) >= 2
            # Convert CTF to TEF
            results = ctf_to_tef(
                path=str(tmp_dir),
                skip_args=False,
                custom_metadata=CUSTOM_METADATA,
                custom_events=create_custom_events(
                    tvm_op_remove_prefix=args.tvm_model_op_remove_prefix,
                    tvm_op_remove_suffix=args.tvm_model_op_remove_suffix,
                    multi_model_trace=multiple_models,
                    symbol_map=symbol_map,
                ),
            )
            tef_trace, thread_name = results.tef, results.thread_names

            tef_trace = adjust_instrumentation_trace(tef_trace)

    # If TVM inference was detected, scan through trace and recalculate model numbers
    # based on common prefix of used TVM functions
    tvm_prefix_to_model_id = None
    if TVM_EVENTS:
        from extract_tvm_model_data import tvm_recalculate_model_numbers

        # Exclude ID 0 reported by TVM for all models, as TVM models' IDs are recalculated
        # based on the OP prefixes and the trace is updated to contain these IDs
        if 0 in MODEL_IDS_MAPPING:
            MODEL_IDS_MAPPING.pop(0)

        tef_trace, tvm_prefix_to_model_id = tvm_recalculate_model_numbers(
            tef_trace, len(MODEL_IDS_MAPPING)
        )
        MODEL_IDS_MAPPING.update(tvm_prefix_to_model_id)

    if thread_name:
        # Custom metadata event supported by Speedscope to associate ID with thread name
        tef_trace += [
            {
                "name": "thread_name",
                "cat": "zephyr",
                "ph": EventPhase.METADATA.value,
                "pid": 0,
                "tid": tid,
                "args": {"name": t_name},
            }
            for t_name, tid in thread_name.items()
        ]

    # Metadata for TFLM models
    if args.tflm_model_paths:
        from extract_tflite_model_data import extract_model_data

        if args.tflm_model_ids:
            if len(args.tflm_model_ids) != len(args.tflm_model_paths):
                raise ValueError(
                    "Number of elements in --tflm-model-ids does not match with --tflm-model-paths"
                )
            args.tflm_model_ids = [int(model_id, 16) for model_id in args.tflm_model_ids]
        else:
            args.tflm_model_ids = [None] * len(args.tflm_model_paths)

        for tflm_model, model_id in zip(args.tflm_model_paths, args.tflm_model_ids):
            metadata = extract_model_data(
                tflm_model, args.zephyr_base, args.zephyr_elf_path, model_id
            )
            if multiple_models:
                for model_id in metadata.get("id", []):
                    if model_id not in MODEL_IDS_MAPPING:
                        print(
                            f"Cannot match model ID (0x{metadata['id']:x}) with IDs reported in the"
                            f" trace ({', '.join([f'0x{k:x}' for k in MODEL_IDS_MAPPING.keys()])})"
                            f" for `{tflm_model}`. The trace may not be displayed correctly, please"
                            " provide valid model IDs manually with --tflm-model-ids flag"
                        )
            if "id" not in metadata:
                add_model_metadata(tef_trace, metadata)
            else:
                # If multiple model IDs were found, create metadata event
                # for each one of them
                for model_id in metadata["id"]:
                    add_model_metadata(tef_trace, metadata | {"id": model_id})

    # Metadata about TVM model
    if args.tvm_model_paths is not None:
        from extract_tvm_model_data import extract_models_data

        for metadata in extract_models_data(
            args.tvm_model_paths,
            args.tvm_model_metadata_paths,
            args.tvm_model_op_remove_prefix,
            args.tvm_model_op_remove_suffix,
            tvm_prefix_to_model_id,
        ):
            add_model_metadata(tef_trace, metadata)

    # Metadata with memory symbols
    if REGION_SIZES:
        mem_symbols = extract_memory_symbols(symbol_map)
        tef_trace.append(
            {
                "name": "MEMORY::SYMBOLS",
                "cat": "zephyr",
                "ph": EventPhase.METADATA.value,
                "pid": 0,
                "tid": 0,
                "ts": 0,
                "args": mem_symbols,
            },
        )

        ram_report: Path = args.build_dir / "ram.json"
        if ram_report.exists():
            with ram_report.open("r") as fd:
                ram = json.load(fd)["symbols"]

            process_ram_report(ram)
            tef_trace.append(
                {
                    "name": "MEMORY::STATICALLY_ASSIGNED_MEM",
                    "cat": "zephyr",
                    "ph": EventPhase.METADATA.value,
                    "pid": 0,
                    "tid": 0,
                    "ts": 0,
                    "args": ram["size"],
                },
            )

    if args.trim_metadata:
        tef_trace = trim_metadata(tef_trace)

    # Print or save the result
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w") as fd:
            json.dump(tef_trace, fd)
    else:
        print(json.dumps(tef_trace, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "prepare_trace",
        description=__doc__,
        allow_abbrev=False,
    )
    parser = setup_parser(parser)
    args = parser.parse_args(sys.argv[1:])

    prepare(args)
