# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides microTVM model data extractor.
"""

import argparse
import re
from pathlib import Path

import yaml

PARAM_NODE_RE = re.compile(r"p\d+")


def extract_model_data(model_graph_path: Path) -> dict:
    """
    Extracts model hyperparameters from model graph file.

    Parameters
    ----------
    model_graph_path : Path
        Path to the model graph.

    Returns
    -------
    dict
        Dict with model data.
    """
    if not model_graph_path.exists():
        raise ValueError(f"Provided model path does not exist {model_graph_path}")

    with open(model_graph_path) as model_graph_f:
        model_graph = yaml.safe_load(model_graph_f)

    model_data = dict()

    shapes = model_graph["attrs"]["shape"][1]
    dtypes = model_graph["attrs"]["dltype"][1]

    input_nodes = []
    output_nodes = []

    for node_idx, node in enumerate(model_graph["nodes"]):
        if PARAM_NODE_RE.match(node["name"]) is None and node["op"] == "null":
            input_nodes.append((node_idx, node))

    for head, _, _ in model_graph["heads"]:
        output_nodes.append((head, model_graph["nodes"][head]))

    for io_type, io_nodes in (("inputs", input_nodes), ("outputs", output_nodes)):
        model_data[io_type] = []
        for node_idx, node in io_nodes:
            io_data = dict()

            io_data["name"] = node["name"]
            io_data["shape"] = shapes[node_idx][:]
            io_data["dtype"] = dtypes[node_idx][:]

            model_data[io_type].append(io_data)

    model_data["tensors"] = []
    model_data["ops"] = []
    for node_idx, node in enumerate(model_graph["nodes"]):
        tensor_data = dict()

        tensor_data["name"] = node["name"]
        tensor_data["index"] = node_idx
        tensor_data["shape"] = shapes[node_idx][:]
        tensor_data["dtype"] = dtypes[node_idx][:]

        model_data["tensors"].append(tensor_data)

        if node["op"] != "null":
            op_data = dict()

            op_data["op_name"] = node["attrs"]["func_name"]
            op_data["index"] = node_idx
            op_data["flatten"] = node["attrs"]["flatten_data"] == "1"
            for attr in ("out_layout", "data_layout", "kernel_layout"):
                if node["attrs"].get(attr, False):
                    op_data[attr] = node["attrs"][attr]

            op_data["inputs"] = [inp[0] for inp in node["inputs"]]
            op_data["outputs"] = [node_idx]
            op_data["inputs_types"] = [dtypes[inp][:] for inp in op_data["inputs"]]
            op_data["output_types"] = [dtypes[inp][:] for inp in op_data["outputs"]]
            op_data["inputs_shapes"] = {inp: shapes[inp][:] for inp in op_data["inputs"]}
            op_data["output_shapes"] = {inp: shapes[inp][:] for inp in op_data["outputs"]}

            model_data["ops"].append(op_data)

    return model_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script for extracting microTVM model information",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--model-graph-path",
        type=Path,
        required=True,
        help="Path to the microTVM model graph",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        required=True,
        help="Path where extracted data will be saved in yaml format",
    )

    args = parser.parse_args()

    model_data = extract_model_data(args.model_graph_path)

    with open(args.output_path, "w") as out_f:
        yaml.safe_dump(model_data, out_f, sort_keys=False)

    print(f"Data saved to {args.output_path}")
