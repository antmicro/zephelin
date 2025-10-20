# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides microTVM model data extractor.
"""

import argparse
import inspect
import json
import math
import re
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable, Iterator

import yaml

if TYPE_CHECKING:
    import tvm


PARAM_NODE_RE = re.compile(r"p\d+")
DEFAULT_OP_SUFFIX_RE = re.compile(r"_\d*$")
DEFAULT_OP_PREFIX_RE = re.compile("^tvmgen_default_")


class IRParser:
    """Class for parsing TVM Intermediate Representation and operators parameters extraction."""

    def __init__(self, tvm_error_ok: bool = False):
        """
        Creates class instance and patches `tvm.ir.json_compact`.

        Parameters
        ----------
        tvm_error_ok : bool
            Determines whether TVM related errors should raise an exception.
        """
        from tvm.ir.base import json_compact

        self.tvm_error_ok = tvm_error_ok
        self.create_updater_original = json_compact.create_updater
        self.upgrade_json_original = json_compact.upgrade_json
        self.create_updater_16_to_17_original = getattr(
            json_compact, "create_updater_16_to_17", lambda: lambda data: data
        )
        json_compact.create_updater = self.create_updater
        json_compact.create_updater_16_to_17 = self.create_updater_16_to_17
        json_compact.upgrade_json = self.upgrade_json

    def create_updater(self, node_map: dict, from_ver: str, to_ver: str) -> Callable[[dict], dict]:
        """Adds `struct_info_` fields to all nodes since version 0.16."""

        def _initialize_struct_info(node):
            node["attrs"].setdefault("struct_info_", "0")
            return node

        if from_ver != "0.15" or to_ver != "0.16":
            return self.create_updater_original(node_map, from_ver, to_ver)

        def _updater(data: dict) -> dict:
            # Trick to update all nodes, standard upgrading procedure
            # allows to define updaters only for specific node types.
            data = self.create_updater_original(node_map, from_ver, to_ver)(data)
            for node in data["nodes"]:
                if "_checked_type_" in node.get("attrs", {}):
                    node = _initialize_struct_info(node)
            return data

        return _updater

    def create_updater_16_to_17(self):
        """Adds `disable_predication` field to the `Split` node."""

        def _initialize_disable_prediction(node, _):
            node["attrs"].setdefault("disable_predication", "0")
            return node

        def _updater(data):
            data = self.create_updater_16_to_17_original()(data)
            data["attrs"]["tvm_version"] = "0.16"
            node_map = {"Split": _initialize_disable_prediction}
            data = self.create_updater(node_map, "0.16", "0.17")(data)
            return data

        return _updater

    def create_updater_17_to_18(self):
        """Updates `TargetKind` node."""

        def _update_target_kind(node, nodes):
            idx = int(node["attrs"]["name"])
            node["repr_str"] = nodes[idx]["repr_str"]
            del node["attrs"]
            return node

        return self.create_updater({"TargetKind": _update_target_kind}, "0.17", "0.18")

    def downgrade_18(self, data: dict):
        """
        TVM version 0.18.0 introduces `Box` types which cannot be parsed by older versions. However,
        it still generates legacy nodes, therefore this function changes links to boxed objects to
        their corresponding legacy nodes.
        """
        nodes = data["nodes"]
        legacy_nodes = {
            value: node
            for node in nodes
            if (attrs := node.get("attrs"))
            if "dtype" in attrs
            if (value := attrs.get("value"))
        }

        for node in nodes:
            if (
                not (type_key := node.get("type_key"))
                or not type_key.startswith("runtime.Box")
                or not (legacy_node := legacy_nodes.get(node["repr_str"]))
            ):
                continue

            node.clear()
            node.update(legacy_node)

    def upgrade_json(self, json_str: str) -> str:
        """
        Performs built-in TVM IR upgrade procedure, custom fixes, and reversing the upgrade with
        breaking changes, if needed.
        """
        import tvm

        data = json.loads(json_str)
        allow_not_upgraded = False
        model_version = data["attrs"]["tvm_version"]
        lib_version = tvm.__version__
        if model_version >= "0.18" and ("0.18" > lib_version or lib_version == "0.18.dev0"):
            allow_not_upgraded = True
            self.downgrade_18(data)

        try:
            data = json.loads(self.upgrade_json_original(json.dumps(data)))
            if data["attrs"]["tvm_version"].startswith("0.17"):
                data = self.create_updater_17_to_18()(data)
        except ValueError as ex:
            if "Cannot update" not in str(ex) or not allow_not_upgraded:
                raise

        return json.dumps(data)

    def find_parameters(self, obj: "tvm.runtime.Object | Iterable") -> Iterator["tvm.ir.Attrs"]:
        """Traverses IR and collects operators parameters."""
        from tvm.runtime import Object

        typename = type(obj).__name__
        if isinstance(obj, Object):
            typename += obj.legacy_repr().partition("(")[0]

        if "Attrs" in typename and "Dict" not in typename:
            yield obj
            return

        if "__getitem__" in dir(obj) and "Dict" not in typename and not isinstance(obj, str):
            for a in obj:
                yield from self.find_parameters(a)
            return

        # Traversing children
        for field in ("args", "attrs", "body"):
            yield from self.find_parameters(getattr(obj, field, []))

    def ir_to_JSON_serializable(self, obj: "tvm.runtime.Object"):
        """Converts TVM wrappers into serializable types."""
        if "__getitem__" in dir(obj) and not isinstance(obj, str):
            return [self.ir_to_JSON_serializable(item) for item in obj]
        elif (value := getattr(obj, "value", None)) is not None:
            return value
        return repr(obj)

    def convert_attrs(self, attrs: "tvm.ir.Attrs") -> dict:
        """Serializes attributes object."""
        serialized = {}
        for name in dir(attrs):
            is_internal = name.startswith("__") or name == "handle"
            if is_internal:
                continue

            value = getattr(attrs, name, None)
            is_method = inspect.ismethod(value)
            is_empty = value is None or str(value) == ""
            if is_method or is_empty:
                continue

            serialized[name] = self.ir_to_JSON_serializable(value)
        return serialized

    def parse_ops_parameters(self, model_metadata_path: Path) -> tuple[dict, str | None]:
        """
        Loads TVM IR, parses it, and extracts operators parameters.

        Parameters
        ----------
        model_metadata_path : Path
            The path to file with model's metadata.

        Returns
        -------
        dict
            Extracted operators parameters
        str | None
            Common prefix of TVM functions or None
        """
        import tvm.ir

        if not model_metadata_path.exists():
            raise ValueError(f"Provided model metadata path does not exist {model_metadata_path}")

        ops_parameters = {}
        func_names = set()
        try:
            data = json.loads(model_metadata_path.read_text())
            function_metadata = tvm.ir.load_json(json.dumps(data))

            for op_name, op in function_metadata.items():
                # Skip generic tvm_main function
                # and all reshape functions as they are the same as __nop
                if op_name == "__tvm_main__" or re.match(r".*_reshape(?:_[0-9]+)?", op_name):
                    continue

                func_names.add(op_name)
                for attrs in self.find_parameters(op.relay_primfuncs.items()):
                    ops_parameters[op_name] = ops_parameters.get(op_name, {})
                    ops_parameters[op_name] |= self.convert_attrs(attrs)
        except Exception as ex:
            if not self.tvm_error_ok:
                raise
            print(f"Failed to analyze model metadata: {ex}")

        return ops_parameters, get_common_prefix(list(func_names))


def common_prefix_bisect(a: str, b: str) -> str | None:
    """
    Bisects two strings in order to find common prefix.

    Parameters
    ----------
    a : str
        First string
    b : str
        Second string

    Returns
    -------
    str | None
        Found common prefix or None
    """
    lo = 0
    hi = min(len(a), len(b)) + 1
    while lo < hi:
        mid = (lo + hi) // 2
        if b[:mid] != a[:mid]:
            hi = mid
        else:
            lo = mid + 1
    return a[: lo - 1] if lo >= 1 else None


def get_common_prefix(func_names: list[str]) -> str | None:
    """
    Updates common prefix with a new string.

    Parameters
    ----------
    func_names : list[str]
        List of strings from which common prefix will be find

    Returns
    -------
    str | None
        Found common prefix
    """
    common_prefix = None
    if len(func_names) >= 2:
        common_prefix = common_prefix_bisect(func_names[0], func_names[1])
        for func_name in func_names[2:]:
            if func_name.startswith(common_prefix):
                continue
            ln = min(len(common_prefix), len(func_name))
            common_prefix = common_prefix_bisect(common_prefix[:ln], func_name[:ln])
            if common_prefix is None:
                break
    elif len(func_names) == 1:
        common_prefix = func_names[0]
    else:
        print("Missing tvm_op functions, common prefix will not be deduced")
    return common_prefix


def get_graph_tvmgen_prefix(model_graph: dict) -> str | None:
    """
    Calculates common prefix of tvmgen function from model graph file.

    Parameters
    ----------
    model_graph : dict
        The JSON representation of model's graph

    Returns
    -------
    str | None
        The common prefix or None
    """
    op_nodes = [n for n in model_graph["nodes"] if n["op"] == "tvm_op"]
    op_func_name = [n["attrs"]["func_name"] for n in op_nodes if n["attrs"]["func_name"] != "__nop"]
    return get_common_prefix(op_func_name)


def tvm_recalculate_model_numbers(tef_trace: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """
    Adjusts names and arguments of INFERENCE and MODEL events based on used functions' prefixes.

    Parameters
    ----------
    tef_trace : list[dict]
        The trace in Trace Event Format

    Returns
    -------
    list[dict]
        Updated TEF trace
    dict[str, int]
        Mapping of tvmgen prefix to the ID of model
    """
    from prepare_trace import INFERENCE_EVENT_NAME, MODEL_EVENT_NAME, TVMGEN_PREFIX_ARG

    thread_inference_start = {}
    prefix_to_model_number = {}
    for i, event in enumerate(tef_trace):
        if not event["name"].startswith(INFERENCE_EVENT_NAME):
            continue
        # Processing INFERENCE::MODEL events
        thread_id = event["tid"]
        # Remember beginning of inference
        if event["ph"] == "B":
            thread_inference_start[thread_id] = i
            continue
        if event["ph"] != "E":
            continue
        # Processing INFERENCE::MODEL end events
        if thread_inference_start.get(thread_id, None) is None:
            continue
        common_prefix = event["args"].get(TVMGEN_PREFIX_ARG, None)
        if common_prefix is None:
            thread_inference_start[thread_id] = None
            continue
        if common_prefix not in prefix_to_model_number:
            # When inference was interrupted common_prefix can be too long,
            # therefore we need to check, whether it is not one of the already existing ones
            for prefix in prefix_to_model_number:
                if common_prefix.startswith(prefix):
                    common_prefix = prefix
                    break
        if common_prefix not in prefix_to_model_number:
            prefix_to_model_number[common_prefix] = len(prefix_to_model_number)
        model_num = prefix_to_model_number[common_prefix]
        inference_start_id = thread_inference_start[thread_id]
        # Update model events names to contain new model number
        for model_event in [
            e
            for e in tef_trace[inference_start_id + 1 : i]
            if e["name"].startswith(MODEL_EVENT_NAME) and e["tid"] == thread_id
        ]:
            model_event["name"] = re.sub(
                rf"{MODEL_EVENT_NAME}[0-9]*::",
                f"{MODEL_EVENT_NAME}{model_num}::",
                model_event["name"],
            )
        # Update inference events and its model ids
        for e in (event, tef_trace[thread_inference_start[thread_id]]):
            e["name"] = f"{INFERENCE_EVENT_NAME}{model_num}"
            e["args"]["model_id"] = model_num
        del event["args"][TVMGEN_PREFIX_ARG]
        thread_inference_start[thread_id] = None
    return tef_trace, prefix_to_model_number


def extract_model_data(
    model_graph_path: Path,
    prefix_to_model_metadata: dict[str, dict] | None = None,
    model_op_remove_prefix: re.Pattern = DEFAULT_OP_PREFIX_RE,
    model_op_remove_suffix: re.Pattern = DEFAULT_OP_SUFFIX_RE,
    prefix_to_model_id: dict[str, int] | None = None,
) -> dict:
    """
    Extracts model hyperparameters from model graph file.

    Parameters
    ----------
    model_graph_path : Path
        Path to the model graph.
    prefix_to_model_metadata : dict[str, dict] | None
        Mapping of functions' common prefix to model metadata.
    model_op_remove_prefix : re.Pattern
        Pattern removing TVM operator prefix.
    model_op_remove_suffix : re.Pattern
        Pattern removing TVM operator type suffix.
    prefix_to_model_id : dict[str, int] | None
        Mapping of common prefix to model's ID.

    Returns
    -------
    dict
        Dict with model data.
    """
    if not model_graph_path.exists():
        raise ValueError(f"Provided model path does not exist {model_graph_path}")

    with open(model_graph_path) as model_graph_f:
        model_graph = yaml.safe_load(model_graph_f)

    model_id = None
    tvmgen_prefix = get_graph_tvmgen_prefix(model_graph)
    if prefix_to_model_id and tvmgen_prefix not in prefix_to_model_id:
        print(f"Prefix {tvmgen_prefix} not in map")
    elif not prefix_to_model_id:
        print("Missing prefix_to_model_id, metadata may not be matched properly with the model")
    else:
        model_id = prefix_to_model_id[tvmgen_prefix]

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

    def get_op_type_name(name: str):
        name = model_op_remove_prefix.sub("", name)
        name = model_op_remove_suffix.sub("", name)
        return name

    def get_op_type(name: str):
        return model_op_remove_prefix.sub("", name)

    for io_type, io_nodes in (("inputs", input_nodes), ("outputs", output_nodes)):
        model_data[io_type] = []
        for node_idx, node in io_nodes:
            io_data = dict()

            io_data["name"] = get_op_type(node["name"])
            io_data["shape"] = shapes[node_idx][:]
            io_data["dtype"] = dtypes[node_idx][:]

            model_data[io_type].append(io_data)

    try:
        from tvm import DataType

        def set_dtype_size(data: dict):
            dtype = DataType(data["dtype"])
            itemsize = (dtype.bits * dtype.lanes + 7) // 8
            data["size"] = itemsize * math.prod(data["shape"])

    except ModuleNotFoundError:
        print("TVM python package is not installed, skipping layer size calculation")

        def set_dtype_size(data: dict):
            pass

    ops_parameters = prefix_to_model_metadata.get(tvmgen_prefix, {})

    model_data["tensors"] = []
    model_data["ops"] = []
    for node_idx, node in enumerate(model_graph["nodes"]):
        tensor_data = dict()

        tensor_data["name"] = get_op_type(node["name"])
        tensor_data["index"] = node_idx
        tensor_data["shape"] = shapes[node_idx][:]
        tensor_data["dtype"] = dtypes[node_idx][:]
        set_dtype_size(tensor_data)

        model_data["tensors"].append(tensor_data)

        if node["op"] != "null":
            op_data = dict()

            name = node["attrs"]["func_name"]
            op_data["op_name"] = get_op_type_name(name)
            op_data["index"] = node_idx

            op_data["inputs"] = [inp[0] for inp in node["inputs"]]
            op_data["outputs"] = [node_idx]
            op_data["inputs_types"] = [dtypes[inp][:] for inp in op_data["inputs"]]
            op_data["output_types"] = [dtypes[inp][:] for inp in op_data["outputs"]]
            op_data["inputs_shapes"] = {inp: shapes[inp][:] for inp in op_data["inputs"]}
            op_data["output_shapes"] = {inp: shapes[inp][:] for inp in op_data["outputs"]}

            op_parameters = ops_parameters.get(name, {})
            op_parameters["flatten"] = node["attrs"]["flatten_data"] == "1"
            op_parameters |= {
                attr: value
                for attr in ("out_layout", "data_layout", "kernel_layout")
                if (value := node["attrs"].get(attr, False))
            }
            if op_parameters:
                op_data["parameters"] = op_parameters

            model_data["ops"].append(op_data)

    if model_id is not None:
        model_data["id"] = model_id

    return model_data


def extract_models_data(
    model_graph_paths: list[Path],
    model_metadata_paths: list[Path] | None = None,
    model_op_remove_prefix: re.Pattern = DEFAULT_OP_PREFIX_RE,
    model_op_remove_suffix: re.Pattern = DEFAULT_OP_SUFFIX_RE,
    prefix_to_model_id: dict[str, int] | None = None,
) -> list[dict]:
    """
    Extracts model hyperparameters from model graph file.

    Parameters
    ----------
    model_graph_paths : list[Path]
        List with path to the model graph.
    model_metadata_paths : list[Path] | None
        List with path to the model metadata.
    model_op_remove_prefix : re.Pattern
        Pattern removing TVM operator prefix.
    model_op_remove_suffix : re.Pattern
        Pattern removing TVM operator type suffix.
    prefix_to_model_id : dict[str, int] | None
        Mapping of common prefix to model's ID.

    Returns
    -------
    list[dict]
        List with model data.
    """
    prefix_to_metadata = {}

    for model_metadata_path in model_metadata_paths or []:
        ops_parameters = {}
        tvmgen_prefix = None
        if model_metadata_path is not None:
            try:
                ops_parameters, tvmgen_prefix = IRParser(tvm_error_ok=True).parse_ops_parameters(
                    model_metadata_path
                )
            except ModuleNotFoundError:
                print("TVM python package is not installed, skipping metadata parsing")
        if tvmgen_prefix in prefix_to_metadata:
            print(f"Prefix {tvmgen_prefix} overlaps for metadata")
        prefix_to_metadata[tvmgen_prefix] = ops_parameters
    return [
        extract_model_data(
            model_path,
            prefix_to_metadata,
            model_op_remove_prefix,
            model_op_remove_suffix,
            prefix_to_model_id,
        )
        for model_path in model_graph_paths
    ]


def argparse_regex(value: str) -> re.Pattern:
    """Custom `argparse` type for validating regex patterns."""
    try:
        return re.compile(value)
    except re.error as error:
        raise argparse.ArgumentTypeError(f"Invalid regex: {error}")


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
        "--model-metadata-path",
        type=Path,
        help="Path to the microTVM model metadata",
    )
    parser.add_argument(
        "--model-op-remove-prefix",
        type=argparse_regex,
        help="Pattern removing TVM operator prefix",
        default=DEFAULT_OP_PREFIX_RE,
    )
    parser.add_argument(
        "--model-op-remove-suffix",
        type=argparse_regex,
        help="Pattern removing TVM operator type suffix.",
        default=DEFAULT_OP_SUFFIX_RE,
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        required=True,
        help="Path where extracted data will be saved in yaml format",
    )

    args = parser.parse_args()

    model_data = extract_model_data(
        args.model_graph_path,
        args.model_metadata_path,
        args.model_op_remove_prefix,
        args.model_op_remove_suffix,
    )

    with open(args.output_path, "w") as out_f:
        yaml.safe_dump(model_data, out_f, sort_keys=False)

    print(f"Data saved to {args.output_path}")
