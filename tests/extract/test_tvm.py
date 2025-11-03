# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Tests TVM model data conversion/extraction functions."""

from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

import yaml
from export_tvm_metadata import sample_tvm_metadata_export
from extract_tvm_model_data import IRParser, get_graph_tvmgen_prefix
from pytest import mark

ZEPHELIN_ROOT = Path(__file__).parents[2]
TVM_MODELS_DIR = ZEPHELIN_ROOT / "samples" / "common" / "tvm" / "model"
TFLM_MODELS_DIR = ZEPHELIN_ROOT / "samples" / "common" / "tflm" / "model"


@contextmanager
def generate_metadata(model_path: Path | None = None, module_name: str | None = None):
    """
    Context manager creating temporary file with model's metadata.
    """
    with NamedTemporaryFile() as file:
        sample_tvm_metadata_export(
            tflite_model_path=model_path,
            tvm_model_metadata_path=Path(file.name),
            module_name=module_name,
        )
        yield Path(file.name)


def test_metadata_export():
    """Tests metadata extraction and parsing."""
    with generate_metadata() as metadata:
        params, module_prefix = IRParser(tvm_error_ok=False).parse_ops_parameters(metadata)
    assert params == {
        "tvmgen_default_fused_nn_dense": {"units": 4},
        "tvmgen_default_fused_nn_max_pool2d_1": {
            "ceil_mode": "0",
            "dilation": [1, 1],
            "layout": "'NHWC'",
            "padding": [0, 0, 0, 0],
            "pool_size": [3, 1],
            "strides": [3, 1],
        },
        "tvmgen_default_fused_nn_conv2d_nn_bias_add_nn_relu": {
            "channels": 8,
            "data_layout": "'NHWC'",
            "dilation": [1, 1],
            "groups": "1",
            "kernel_layout": "'HWIO'",
            "kernel_size": [4, 3],
            "padding": [1, 1, 2, 1],
            "strides": [1, 1],
            "axis": "3",
        },
        "tvmgen_default_fused_nn_dense_nn_relu": {"units": 16},
        "tvmgen_default_fused_nn_softmax": {"axis": "-1"},
        "tvmgen_default_fused_nn_max_pool2d": {
            "ceil_mode": "0",
            "dilation": [1, 1],
            "layout": "'NHWC'",
            "padding": [0, 0, 0, 0],
            "pool_size": [3, 3],
            "strides": [3, 3],
        },
        "tvmgen_default_fused_nn_conv2d_nn_bias_add_nn_relu_1": {
            "channels": 16,
            "data_layout": "'NHWC'",
            "dilation": [1, 1],
            "groups": "1",
            "kernel_layout": "'HWIO'",
            "kernel_size": [4, 1],
            "padding": [1, 0, 2, 0],
            "strides": [1, 1],
            "axis": "3",
        },
    }
    assert module_prefix == "tvmgen_default_fused_nn_"


def test_magic_wand_module_name():
    """
    Tests module name extraction with custom value.
    """
    with generate_metadata(TFLM_MODELS_DIR / "magic-wand.tflite", "test") as metadata:
        _, module_prefix = IRParser(tvm_error_ok=False).parse_ops_parameters(metadata)
    assert module_prefix == "tvmgen_test_fused_nn_"


@mark.parametrize(
    "graph_file,metadata_file,module_name",
    [
        (
            TVM_MODELS_DIR / "magic-wand-graph.json",
            TVM_MODELS_DIR / "magic-wand-metadata.json",
            "tvmgen_default_fused_nn_",
        ),
        (
            TVM_MODELS_DIR / "sine-graph.json",
            TVM_MODELS_DIR / "sine-metadata.json",
            "tvmgen_quantized_fused_",
        ),
    ],
)
def test_graph_metadata_module_name(graph_file: Path, metadata_file: Path, module_name: str):
    """
    Tests whether module names extracted from graph and metadata files are the same
    and matches the true value.
    """
    _, metadata_module_prefix = IRParser(tvm_error_ok=False).parse_ops_parameters(metadata_file)

    with graph_file.open() as model_graph_f:
        model_graph = yaml.safe_load(model_graph_f)
    graph_module_prefix = get_graph_tvmgen_prefix(model_graph)

    assert graph_module_prefix == metadata_module_prefix
    assert graph_module_prefix == module_name
