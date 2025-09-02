# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides sample code to generate TVM model metadata.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tflite
    from tvm.relay.backend.executor_factory import GraphExecutorFactoryModule


def sample_tflite_model() -> bytes:
    """
    Creates sample model.
    """
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

    import keras
    import tensorflow as tf

    inputs = keras.Input(shape=(128, 3, 1))
    x = keras.layers.Conv2D(kernel_size=(4, 3), filters=8, activation="relu", padding="same")(
        inputs
    )
    x = keras.layers.MaxPooling2D((3, 3))(x)
    x = keras.layers.Conv2D(kernel_size=(4, 1), filters=16, activation="relu", padding="same")(x)
    x = keras.layers.MaxPooling2D((3, 1), padding="same")(x)
    x = keras.layers.Flatten()(x)
    x = keras.layers.Dense(16, activation="relu")(x)
    outputs = keras.layers.Dense(4, activation="softmax")(x)
    model = keras.Model(inputs=inputs, outputs=outputs)
    model.compile()
    return tf.lite.TFLiteConverter.from_keras_model(model).convert()


def sample_tvm_compile(tflite_model: tflite.Model) -> GraphExecutorFactoryModule:
    """
    Compiles TFLite model with default parameters.
    """
    import tvm.relay

    mod, params = tvm.relay.frontend.from_tflite(tflite_model)
    return tvm.relay.build(mod, params=params, target="c")


def sample_tvm_metadata_export(
    tflite_model_path: Path | None = None,
    tvm_model_path: Path | None = None,
    tvm_model_graph_path: Path | None = None,
    tvm_model_metadata_path: Path | None = None,
):
    """
    Builds TVM model from TFLite one and extracts metadata.

    Parameters
    ----------
    tflite_model_path : Path | None
        Path to TFLite model. If not provided, `sample_tflite_model` is used to generate sample one.
    tvm_model_path : Path | None
        Path to the TVM model to extract
    tvm_model_graph_path : Path | None
        Path to the TVM model graph to extract
    tvm_model_metadata_path : Path | None
        Path to the model metadata to extract
    """
    import tflite
    import tvm.ir

    # Read or generate TFLite model
    if tflite_model_path:
        print(f"Using provided model: {tflite_model_path}")
        buf = tflite_model_path.read_bytes()
    else:
        print("Using sample model")
        buf = sample_tflite_model()
    tflite_model = tflite.Model.GetRootAsModel(buf)

    # Compile and extract metadata
    module = sample_tvm_compile(tflite_model)
    metadata = module.function_metadata

    # Optionally, save TVM model
    if tvm_model_path:
        print(f"Exporting TVM model to {tvm_model_path}")
        module.export_library(tvm_model_path)
    if tvm_model_graph_path:
        print(f"Exporting TVM model graph to {tvm_model_graph_path}")
        graph_json = module.get_graph_json()
        tvm_model_graph_path.write_text(graph_json)

    # Print or save metadata
    if tvm_model_metadata_path:
        print(f"Exporting model metadata to {tvm_model_metadata_path}")
        tvm_model_metadata_path.write_text(tvm.ir.save_json(metadata))
    else:
        print(f"Metadata:\n{metadata}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script for extracting microTVM model metadata",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--tflite-model-path",
        type=Path,
        help="Path to TFLite model",
    )
    parser.add_argument(
        "--tvm-model-path",
        type=Path,
        help="Path to the TVM model to extract",
    )
    parser.add_argument(
        "--tvm-model-graph-path",
        type=Path,
        help="Path to the TVM model graph to extract",
    )
    parser.add_argument(
        "--tvm-model-metadata-path",
        type=Path,
        help="Path to the model metadata to extract",
    )

    args = parser.parse_args()

    sample_tvm_metadata_export(
        tflite_model_path=args.tflite_model_path,
        tvm_model_path=args.tvm_model_path,
        tvm_model_graph_path=args.tvm_model_graph_path,
        tvm_model_metadata_path=args.tvm_model_metadata_path,
    )
