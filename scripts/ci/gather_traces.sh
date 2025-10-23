#!/bin/bash

# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

set -xeuo pipefail

BOARD=${BOARD:-max32690fthr/max32690/m4}
CTF_CONFS=${CTF_CONFS:-"-DCONFIG_ZPL_TRACE_FORMAT_CTF=y
-DCONFIG_TRACING_BUFFER_SIZE=10000 -DCONFIG_BOOT_BANNER=n -DCONFIG_PRINTK=n -DCONFIG_LOG=n"}


### TFLM profiler
west build -p -b $BOARD samples/profiling/tflm_profiler -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./channel0_0 --timeout 45
west zpl-prepare-trace ./channel0_0 \
  --tflm-model-path ./samples/common/tflm/model/magic-wand.tflite \
  -o ./tef_tflm_profiler.json

### Memory profiling
west build -p -b $BOARD samples/profiling/memory_profiling -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./channel0_0 --timeout 45
west zpl-prepare-trace ./channel0_0 -o ./tef_memory_profiling.json

### TVM profiler
west build -p -b $BOARD samples/profiling/tvm_profiler -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./channel0_0 --timeout 45
west zpl-prepare-trace ./channel0_0 \
  --tvm-model-path ./samples/common/tvm/model/magic-wand-graph.json \
  --tvm-model-metadata-path ./samples/common/tvm/model/magic-wand-metadata.json \
  -o ./tef_tvm_profiler.json

### Marking code scopes
west build -p -b $BOARD samples/basic/marking_code_scopes -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./channel0_0 --timeout 45
west zpl-prepare-trace ./channel0_0 -o ./tef_marking_code_scopes.json

### CPU load
west build -p -b $BOARD samples/profiling/cpu_load -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./channel0_0 --timeout 45
west zpl-prepare-trace ./channel0_0 -o ./tef_cpu_load.json

### TFLM multi model
west build -p -b $BOARD samples/profiling/tflm_multi_model -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./channel0_0 --timeout 45
west zpl-prepare-trace ./channel0_0 -o ./tef_tflm_multi_model.json \
  --tflm-model-paths ./samples/common/tflm/model/magic-wand.tflite \
    ./samples/common/tflm/model/sine.tflite

### TVM multi model
west build -p -b $BOARD samples/profiling/tvm_multi_model -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./channel0_0 --timeout 45
west zpl-prepare-trace ./channel0_0 -o ./tef_tvm_multi_model.json \
  --tvm-model-op-remove-prefix 'tvmgen_[a-zA-Z]+_fused_nn_dense_subtract_add_fixed_point_' \
  --tvm-model-paths ./samples/common/tvm/model/magic-wand-graph.json \
    ./samples/common/tvm/model/sine-graph.json \
  --tvm-model-metadata-paths ./samples/common/tvm/model/magic-wand-metadata.json \
    ./samples/common/tvm/model/sine-metadata.json

# TFLM and TVM models
west build -p -b $BOARD samples/profiling/tflm_tvm_models -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./channel0_0 --timeout 45
west zpl-prepare-trace ./channel0_0 -o ./tef_tflm_tvm_models.json \
  --tflm-model-paths ./samples/common/tflm/model/sine.tflite \
  --tvm-model-paths ./samples/common/tvm/model/sine-graph.json \
    ./samples/common/tvm/model/sine2-graph.json \
  --tvm-model-metadata-paths ./samples/common/tvm/model/sine-metadata.json \
    ./samples/common/tvm/model/sine2-metadata.json \
  --tvm-model-op-remove-prefix 'tvmgen_[a-zA-Z0-9]+_fused_nn_dense_subtract_add_fixed_point_' \
  --trim-metadata
