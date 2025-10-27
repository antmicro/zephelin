# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Script preparing trace (in TEF) based on the CTF trace and metadata, e.g. TFLM model.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import bt2
from ctf2tef import (
    CustomEventDefinition,
    CustomMetadataDefinition,
    EventPhase,
    ctf_to_tef,
    instrumentation_ctf_to_tef,
    prepare_dir,
    prepare_dir_for_instrumentation,
)
from extract_tvm_model_data import (
    DEFAULT_OP_PREFIX_RE,
    DEFAULT_OP_SUFFIX_RE,
    argparse_regex,
)

if TYPE_CHECKING:
    import bt2


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


# The list of custom events definitions
def create_custom_events(
    tvm_op_remove_prefix: re.Pattern = DEFAULT_OP_PREFIX_RE,
    tvm_op_remove_suffix: re.Pattern = DEFAULT_OP_SUFFIX_RE,
    multi_model_trace: bool = False,
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

    Returns
    -------
    list[CustomEventDefinition]
        Created events.
    """
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


def extract_memory_symbols(zephyr_elf_path: Path):
    """
    Extracts memory symbols from the provided Zephyr ELF.

    It uses `nm` from GNU binutils to get all available symbols
    and filteres out ones that have not appeared in trace.
    """
    if not zephyr_elf_path.exists():
        print(
            f"Zephyr ELF ({zephyr_elf_path}) does not exist, memory symbols will not be extracted",
            file=sys.stderr,
        )
        return
    if 0 != subprocess.call(["which", "nm"], stdout=subprocess.DEVNULL):
        print(
            "`nm` is not available, please install binutils to extract symbols of memory regions",
            file=sys.stderr,
        )
        return

    nm = subprocess.run(["nm", str(zephyr_elf_path.absolute())], stdout=subprocess.PIPE)
    if 0 != nm.returncode:
        print("Symbol extraction failed", file=sys.stderr)
        return

    nm_output = nm.stdout.decode()
    addr_to_symbol = defaultdict(list)
    for line in nm_output.splitlines():
        addr, _, name = line.split(" ")
        addr_to_symbol[addr.lower()].append(name)

    mem_symbols = {}
    for addr in REGION_SIZES:
        addr_hex = f"{addr:x}"
        if addr_hex not in addr_to_symbol or not addr_to_symbol[addr_hex]:
            print(f"Cannot find symbol for address 0x{addr_hex}", file=sys.stderr)
            continue
        # Choose last found symbol
        mem_symbols[addr] = addr_to_symbol[addr_hex][-1]

    return mem_symbols


def trim_metadata(tef_trace: list[dict]):
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
                ),
            )
            tef_trace, thread_name = results.tef, results.thread_names
    if args.instrumentation:
        with prepare_dir_for_instrumentation(
            args.instrumentation, args.build_dir / "ctf_metadata"
        ) as tmp_dir:
            instr_trace = instrumentation_ctf_to_tef(
                str(tmp_dir), args.zephyr_elf_path, args.zephyr_base
            ).tef["traceEvents"]
        # Convert timestamps to us
        for event in instr_trace:
            # print(event["ph"], event["ts"])
            event["ts"] = float(event["ts"]) * 1e-3
            # Set all process ID to 0
            event["pid"] = 0
        tef_trace += instr_trace

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
        mem_symbols = extract_memory_symbols(args.zephyr_elf_path)
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
