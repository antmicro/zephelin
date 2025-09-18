# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Tests TVM model data conversion/extraction functions."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from export_tvm_metadata import sample_tvm_metadata_export
from extract_tvm_model_data import IRParser


def test_metadata_export():
    """Tests metadata extraction and parsing."""
    with NamedTemporaryFile() as file:
        sample_tvm_metadata_export(tvm_model_metadata_path=Path(file.name))
        params = IRParser(tvm_error_ok=False).parse_ops_parameters(Path(file.name))
    assert params == {
        "tvmgen_default_fused_reshape_1": {"allowzero": "0", "newshape": [-1, 16]},
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
        "tvmgen_default_fused_reshape": {"allowzero": "0", "newshape": [1, 224]},
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
