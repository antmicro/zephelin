# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides LiteRT (TFLite) model data extractor.
"""

import argparse
import json
import os
import pickle
import shutil
import sys
from contextlib import contextmanager
from itertools import cycle
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

import numpy as np
import yaml
from ai_edge_litert.interpreter import Interpreter
from west.configuration import MalformedConfig
from west.manifest import Manifest
from west.util import WestNotFound

WARNING_MSG_OPS_PARAMETERS = "Skipping operators parameters parsing: {}"


def find_tflite_micro_path(workspace_path: Path) -> Path | None:
    """
    Finds "tflite-micro" module path.

    Parameters
    ----------
    workspace_path : Path
        Path to Zephyr workspace

    Returns
    -------
    Path | None
        Path if module was found, None if it was not found.
    """
    # Find manifest
    try:
        manifest = Manifest.from_topdir(workspace_path)
    except (MalformedConfig, WestNotFound) as ex:
        print(WARNING_MSG_OPS_PARAMETERS.format(f"Could not find West manifest file ({ex})"))
        return None

    # Find "tflite-micro" module
    tflite_project = None
    for project in manifest.projects:
        if project.name == "tflite-micro":
            tflite_project = project
            break
    else:
        print(WARNING_MSG_OPS_PARAMETERS.format("Could not find 'tflite-micro' module"))
        return None

    return Path(manifest.topdir) / tflite_project.path


def check_type(ops_param_name: str, properties: dict) -> str:
    """
    Returns a string literal representing type of parameter `ops_param_name`,
    based on `properties` dict containing type properties.

    Parameters
    ----------
    ops_param_name : str
        Name of the parameter, such as `padding`, `stride_h`, `stride_w`, etc.
    properties : dict
        A dict containing necessary information to infer type, e.g. minimal and maximal
        value of the type.

    Returns
    -------
    str
        Type representation for provided parameter.
    """
    property_dict = properties[ops_param_name]
    match property_dict:
        case {"type": "number"}:
            return "FLOAT32"
        case {"type": "integer", "minimum": min_val, "maximum": max_val}:
            if min_val == 0 and max_val == 2**8 - 1:
                return "UINT8"
            elif min_val == 0 and max_val == 2**16 - 1:
                return "UINT16"
            elif min_val == 0 and max_val == 2**32 - 1:
                return "UINT32"
            elif min_val == 0 and max_val == 2**64 - 1:
                return "UINT64"
            elif min_val == -(2 ** (16 - 1)) and max_val == 2 ** (16 - 1) - 1:
                return "INT16"
            elif min_val == -(2 ** (32 - 1)) and max_val == 2 ** (32 - 1) - 1:
                return "INT32"
            elif min_val == -(2 ** (64 - 1)) and max_val == 2 ** (64 - 1) - 1:
                return "INT64"
        case _:  # default to byte (e.g. for enums)
            return "INT8"


def annotate_ops_types(
    ops_params: list[dict], ops_layer_types: list[str], type_definitions: dict
) -> list[dict]:
    """
    Annotates parameters of supplied list of layers with type information.

    Parameters
    ----------
    ops_params : list[dict]
        Original parameters to process.
    ops_layer_types : list[str]
        Names of layer types, such as `Conv2DOptions`, `Pool2DOptions`.
    type_definitions : dict
        Type information obtained from jsonschema.

    Returns
    -------
    list[dict]
        List of dicts containing original parameter value and type of that value.
    """
    annotated_ops = []

    for ops_param_dict, layer_type in zip(ops_params, ops_layer_types, strict=True):
        if (def_key := f"tflite_{layer_type}") not in type_definitions:
            annotated_ops.append({})
            continue
        definition = type_definitions[def_key]

        if (key_properties := "properties") not in definition:
            annotated_ops.append({})
            continue
        properties = definition[key_properties]

        annotated_ops.append({
            ops_param_name: {
                "value": ops_param_value,
                "type": check_type(ops_param_name, properties),
            }
            for ops_param_name, ops_param_value in ops_param_dict.items()
        })

    return annotated_ops


def extract_ops_parameters(model_path: Path, zephyr_base: Path | None = None) -> list[dict] | None:
    """
    Extracts operators parameters from tflite model file.

    This requires installed 'flatc' binary because flatbuffers Python API does not allow to decode
    enums into strings.

    Parameters
    ----------
    model_path : Path
        Path to the model.
    zephyr_base : Path | None
        Path to a Zephyr repository.

    Returns
    -------
    list[dict] | None
        Extracted parameters or none if error occurred.
    """
    if shutil.which("flatc") is None:
        print(WARNING_MSG_OPS_PARAMETERS.format("'flatc' is not installed"))
        return

    workspace = zephyr_base.parent if zephyr_base else Path(__file__).parent.parent.parent
    tflite_micro_path = find_tflite_micro_path(workspace)
    if not tflite_micro_path:
        return

    schema_path = tflite_micro_path / "tensorflow/compiler/mlir/lite/schema/schema.fbs"

    with TemporaryDirectory() as tmpdir:
        cmd = [
            "flatc",
            "-o",
            tmpdir,
            "--strict-json",
            "--json",
            "--jsonschema",
            str(schema_path),
            "--",
            model_path,
        ]

        ret = run(cmd, capture_output=True)

        if ret.returncode == 0:
            with (Path(tmpdir) / model_path.stem).with_suffix(".json").open() as f:
                model_json = json.load(f)

            with (Path(tmpdir) / "schema.schema.json").open() as f:
                schema_json = json.load(f)

            subgraph, *_ = model_json["subgraphs"]
            operators = subgraph["operators"]
            definitions = schema_json["definitions"]

            ops_params = [op.get("builtin_options", {}) for op in operators]
            ops_layer_types = [op.get("builtin_options_type", "") for op in operators]

            ops_params = annotate_ops_types(ops_params, ops_layer_types, definitions)

            return ops_params

        else:
            msg = ret.stderr.decode()
            try:
                # Omit flatc help output
                [_, error, *_] = msg.split("\n\n")
                error = error.removeprefix("error:")
            except ValueError:
                error = msg
            print(WARNING_MSG_OPS_PARAMETERS.format(error))


@contextmanager
def extend_path(*p: list[Path]):
    """
    Context manager extending PYTHONPATH with provided arguments.

    Parameters
    ----------
    p: list[Path]
        The paths that will be inserted to PYTHONPATH.
    """
    sys_path = sys.path[:]
    sys.path = [str(_p.resolve()) for _p in p] + sys.path
    try:
        yield
    finally:
        sys.path = sys_path


def deduce_model_addr(
    model_path: Path, zephyr_base: Path | None = None, zephyr_elf: Path | None = None
) -> list[int]:
    """
    Decudes the model address based on model data placement in zephyr.bin,
    address of flash region and flatbuffer offset.

    Parameters
    ----------
    model_path : Path
        Path to the model.
    zephyr_base : Path | None
        Path to a Zephyr repository
    zephyr_elf : Path | None
        Path to a Zephyr ELF

    Returns
    -------
    list[int]
        The list with model addresses that matches the model data.
    """
    from flatbuffers.packer import uoffset

    if not model_path.exists():
        raise ValueError(f"Provided model path does not exist {model_path}")
    if not zephyr_elf or not zephyr_elf.exists():
        raise ValueError("Missing path to Zephyr ELF")

    zephyr_bin = zephyr_elf.with_suffix(".bin")

    with model_path.open("rb") as fd:
        model_bin = fd.read()

    with zephyr_bin.open("rb") as fd:
        zephyr_data = fd.read()

    edt = None
    with (
        # Extend path to use Zephyr's devicetree
        extend_path(zephyr_base / "scripts" / "dts" / "python-devicetree" / "src"),
        (zephyr_elf.parent / "edt.pickle").open("rb") as fd,
    ):
        edt = pickle.load(fd)

    if edt is None or "zephyr,flash" not in edt.chosen_nodes:
        return None

    addresses = []
    begin, idx = 0, 0
    while True:
        idx = zephyr_data.find(model_bin, begin)
        if idx <= 0:
            break

        offset = uoffset.unpack(zephyr_data[idx : idx + uoffset.size])[0]
        begin = idx + offset
        addresses.append(begin + edt.chosen_nodes["zephyr,flash"].regs[0].addr)

    return addresses


def params_size(parameters: dict) -> int:
    """
    Compute sum of parameters size in bytes.

    Parameters
    ----------
    parameters : dict
        Annotated layer parameters.

    Returns
    -------
    int
        Size of all parameters in bytes.
    """
    size = 0
    for info in parameters.values():
        match info["type"]:
            case "INT8" | "UINT8":
                size += 1
            case "INT16" | "UINT16":
                size += 2
            case "INT32" | "UINT32" | "FLOAT32":
                size += 4
            case "INT64" | "UINT64":
                size += 8

    return size


def extract_model_data(
    model_path: Path,
    zephyr_base: Path | None = None,
    zephyr_elf: Path | None = None,
    model_id: int | None = None,
) -> dict:
    """
    Extracts model hyperparameters from tflite model file.

    Parameters
    ----------
    model_path : Path
        Path to the model.
    zephyr_base : Path | None
        Path to a Zephyr repository
    zephyr_elf : Path | None
        Path to a Zephyr ELF
    model_id : int | None
        ID of the model, if not provided will be deduced based on model data in zephyr.bin

    Returns
    -------
    dict
        Dict with model data.
    """
    if not model_path.exists():
        raise ValueError(f"Provided model path does not exist {model_path}")

    interpreter = Interpreter(model_path=str(model_path))

    model_data = dict()

    # extract input/output data
    signatures = interpreter.get_signature_list()
    has_serving_default = signatures is not None and "serving_default" in signatures

    for io_type, io_details in (
        ("input", interpreter.get_input_details()),
        ("output", interpreter.get_output_details()),
    ):
        model_data[f"{io_type}s"] = []

        if has_serving_default:
            io_names = signatures["serving_default"][f"{io_type}s"]
        else:
            io_names = [io["name"] for io in io_details]

        for io, io_name in zip(
            io_details,
            io_names,
            strict=False,
        ):
            io_data = dict()
            io_data["name"] = io_name
            io_data["name_long"] = io["name"]
            io_data["shape"] = io["shape"].tolist()
            io_data["shape_signature"] = io["shape_signature"].tolist()
            io_data["dtype"] = io["dtype"].__name__
            io_data["quantization"] = io["quantization"]
            io_data["quantization_parameters"] = {
                "scales": io["quantization_parameters"]["scales"].tolist(),
                "zero_points": io["quantization_parameters"]["zero_points"].tolist(),
                "quantized_dimension": io["quantization_parameters"]["quantized_dimension"],
            }

            model_data[f"{io_type}s"].append(io_data)

    # extract tensors details
    model_data["tensors"] = []

    for subgraph_idx in range(interpreter.num_subgraphs()):
        for tensor in interpreter.get_tensor_details(subgraph_idx):
            tensor_data = {}
            tensor_data["name"] = tensor["name"]
            tensor_data["subgraph_idx"] = subgraph_idx
            tensor_data["index"] = tensor["index"]
            tensor_data["shape"] = tensor["shape"].tolist()
            tensor_data["shape_signature"] = tensor["shape_signature"].tolist()
            # Size calculation
            scales_arr = tensor.get("quantization_parameters", {}).get(
                "scales", np.array([], dtype=np.float32)
            )
            zero_points_arr = tensor.get("quantization_parameters", {}).get(
                "zero_points", np.array([], dtype=np.float32)
            )
            tensor_data["size"] = int(
                np.dtype(tensor["dtype"]).itemsize * tensor["shape"].prod()
                + scales_arr.itemsize * np.prod(scales_arr.shape)
                + zero_points_arr.itemsize * np.prod(zero_points_arr.shape)
            )
            tensor_data["dtype"] = tensor["dtype"].__name__
            tensor_data["quantization"] = tensor["quantization"]
            tensor_data["quantization_parameters"] = {
                "scales": tensor["quantization_parameters"]["scales"].tolist(),
                "zero_points": tensor["quantization_parameters"]["zero_points"].tolist(),
                "quantized_dimension": tensor["quantization_parameters"]["quantized_dimension"],
            }
            model_data["tensors"].append(tensor_data)

    model_data["ops"] = []

    ops_parameters = extract_ops_parameters(model_path, zephyr_base) or cycle([{}])

    for op, parameters in zip(interpreter._get_ops_details(), ops_parameters, strict=True):
        op_data = {}
        op_data["op_name"] = op["op_name"]
        op_data["index"] = op["index"]
        op_data["inputs"] = op["inputs"].tolist()
        op_data["outputs"] = op["outputs"].tolist()
        op_data["inputs_types"] = [op_type.__name__ for op_type in op["operand_types"]]
        op_data["outputs_types"] = [op_type.__name__ for op_type in op["result_types"]]
        op_data["inputs_shapes"] = {
            idx: model_data["tensors"][idx]["shape"][:] for idx in op_data["inputs"]
        }
        op_data["outputs_shapes"] = {
            idx: model_data["tensors"][idx]["shape"][:] for idx in op_data["outputs"]
        }
        op_data["parameters"] = parameters

        op_data["size"] = params_size(parameters)

        model_data["ops"].append(op_data)

    if model_id is not None:
        model_data["id"] = model_id
    elif zephyr_elf and zephyr_elf.exists():
        addr = deduce_model_addr(model_path, zephyr_base, zephyr_elf)
        if addr:
            model_data["id"] = addr
        else:
            print(f"Model address cannot be deduced for {model_path}")
    else:
        print("Missing zephyr.elf file, cannot deduce model address")

    return model_data


def extract_models_data(
    *models_path: list[Path], zephyr_base: Path | None = None, zephyr_elf: Path | None = None
) -> list[dict]:
    """
    Extracts model hyperparameters from tflite model file.

    Parameters
    ----------
    models_path : list[Path]
        Path to the model.
    zephyr_base : Path | None
        Path to a Zephyr repository
    zephyr_elf : Path | None
        Path to a Zephyr ELF

    Returns
    -------
    list[dict]
        List with models data.
    """
    return [extract_model_data(model, zephyr_base, zephyr_elf) for model in models_path]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script for extracting TFLite model information", allow_abbrev=False
    )
    parser.add_argument("--model-path", type=Path, required=True, help="Path to the TFLite model")
    parser.add_argument(
        "--zephyr-base",
        type=Path,
        default=os.environ.get("ZEPHYR_BASE", None),
        help="The path to a Zephyr repository, can be passed with $ZEPHYR_BASE, "
        "otherwise will be deduced based on the script path",
    )
    parser.add_argument("--zephyr-elf", type=Path, default=None, help="The path to a Zephyr ELF")
    parser.add_argument(
        "--output-path",
        type=Path,
        required=True,
        help="Path where extracted data will be saved in yaml format",
    )

    args = parser.parse_args()

    model_data = extract_model_data(args.model_path, args.zephyr_base, args.zephyr_elf)

    with open(args.output_path, "w") as out_f:
        yaml.safe_dump(model_data, out_f, sort_keys=False)

    print(f"Data saved to {args.output_path}")
