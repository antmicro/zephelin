# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Script preparing trace (in TEF) based on the CTF trace and metadata, e.g. TFLM model.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from ctf2tef import (
    CustomEventDefinition,
    CustomMetadataDefinition,
    EventPhase,
    ctf_to_tef,
    prepare_dir,
)


def layer_name(msg) -> str:
    """
    Generates suffix for model event name.
    """
    fields = msg.event.payload_field
    if not fields:
        return ""
    name = str(fields.get("tag", ""))
    if name.startswith("tvmgen_default_"):
        name = name[15:]
    if "subgraph_idx" in fields:
        name += f"_{fields['subgraph_idx']}"
    if "op_idx" in fields:
        name += f"_{fields['op_idx']}"
    return name


# The list of custom events definitions
CUSTOM_EVENTS = [
    CustomEventDefinition(
        "MODEL::",
        "zpl_tflm_enter",
        "zpl_tflm_exit",
        layer_name,
        lambda _: {"runtime": "TFLite Micro"},
    ),
    CustomEventDefinition(
        "MODEL::",
        "zpl_tvm_enter",
        "zpl_tvm_exit",
        layer_name,
        lambda _: {"runtime": "microTVM"},
    ),
]


def memory_data(msg) -> dict:
    """
    Returns additional arguments with memory ragion name.
    """
    if not (args := msg.event.payload_field):
        return {}
    try:
        # Get enum label and remove ZPL_ prefix
        # This will override "memory_region"
        return {"memory_region": args["memory_region"].labels[0][4:]}
    except Exception:
        return {}


# The dictionary of custom metadata events, where the key is CTF event name
# and value is a definition of new metadata event.
CUSTOM_METADATA = {
    "zpl_memory": CustomMetadataDefinition("MEMORY", None, memory_data),
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "prepare_trace",
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
        help="The path to the output, if not provided, the results will be printed to STDOUT",
        default=None,
    )
    parser.add_argument(
        "--zephyr-base",
        type=Path,
        default=os.environ.get("ZEPHYR_BASE", None),
        help="The path to a Zephyr repository, can be passed with $ZEPHYR_BASE, "
        "otherwise will be deduced based on the script path",
    )
    parser.add_argument(
        "--tflm-model-path",
        type=Path,
        help="Path to the TFLM model, extracted information will be appedened "
        "to the final trace as a metadata",
        default=None,
    )
    parser.add_argument(
        "--tvm-model-path",
        type=Path,
        help="Path to the TVM graph file, extracted information will be appedened "
        "to the final trace as a metadata",
        default=None,
    )
    args = parser.parse_args(sys.argv[1:])

    # Convert CTF
    with prepare_dir(args.ctf_trace, args.zephyr_base) as tmp_dir:
        tef_trace, thread_name = ctf_to_tef(str(tmp_dir), False, CUSTOM_METADATA, CUSTOM_EVENTS)

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

    if args.tflm_model_path is not None:
        from extract_tflite_model_data import extract_model_data

        add_model_metadata(tef_trace, extract_model_data(args.tflm_model_path))
    if args.tvm_model_path is not None:
        from extract_tvm_model_data import extract_model_data

        add_model_metadata(tef_trace, extract_model_data(args.tvm_model_path))

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w") as fd:
            json.dump(tef_trace, fd)
    else:
        print(json.dumps(tef_trace, indent=2))
