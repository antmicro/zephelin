# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides LiteRT (TFLite) model data extractor.
"""

import argparse
from pathlib import Path

import yaml
from ai_edge_litert.interpreter import Interpreter


def extract_model_data(model_path: Path) -> dict:
    """
    Extracts model hyperparameters from tflite model file.

    Parameters
    ----------
    model_path : Path
        Path to the model.

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
    for io_type, io_details in (
        ("input", interpreter.get_input_details()),
        ("output", interpreter.get_output_details()),
    ):
        model_data[f"{io_type}s"] = []
        for io, io_name in zip(
            io_details,
            interpreter.get_signature_list()["serving_default"][f"{io_type}s"],
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
        for tensor in interpreter.get_tensor_details(0):
            tensor_data = {}
            tensor_data["name"] = tensor["name"]
            tensor_data["subgraph_idx"] = subgraph_idx
            tensor_data["index"] = tensor["index"]
            tensor_data["shape"] = tensor["shape"].tolist()
            tensor_data["shape_signature"] = tensor["shape_signature"].tolist()
            tensor_data["dtype"] = tensor["dtype"].__name__
            tensor_data["quantization"] = tensor["quantization"]
            tensor_data["quantization_parameters"] = {
                "scales": tensor["quantization_parameters"]["scales"].tolist(),
                "zero_points": tensor["quantization_parameters"]["zero_points"].tolist(),
                "quantized_dimension": tensor["quantization_parameters"]["quantized_dimension"],
            }
            model_data["tensors"].append(tensor_data)

    # extract ops details
    model_data["ops"] = []

    for op in interpreter._get_ops_details():
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

        model_data["ops"].append(op_data)

    return model_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script for extracting TFLite model information", allow_abbrev=False
    )
    parser.add_argument("--model-path", type=Path, required=True, help="Path to the TFLite model")
    parser.add_argument(
        "--output-path",
        type=Path,
        required=True,
        help="Path where extracted data will be saved in yaml format",
    )

    args = parser.parse_args()

    model_data = extract_model_data(args.model_path)

    with open(args.output_path, "w") as out_f:
        yaml.safe_dump(model_data, out_f, sort_keys=False)

    print(f"Data saved to {args.output_path}")
