#!/bin/bash

# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

set -xeuo pipefail

BOARD=${BOARD:-max32690fthr/max32690/m4}
CTF_CONFS=${CTF_CONFS:-"-DCONFIG_ZPL_TRACE_FORMAT_CTF=y
-DCONFIG_TRACING_BUFFER_SIZE=10000 -DCONFIG_BOOT_BANNER=n -DCONFIG_PRINTK=n"}


### TFLM profiler
west build -p -b $BOARD samples/profiling/tflm_profiler -- ${CTF_CONFS}
timeout --preserve-status -s INT 20s python3 ./scripts/run_renode.py --trace-output ./channel0_0
west zpl-prepare-trace ./channel0_0 \
  --tflm-model-path ./samples/common/tflm/model/magic-wand.tflite \
  -o ./tef_tflm_profiler.json

### Memory profiling
west build -p -b $BOARD samples/profiling/memory_profiling -- ${CTF_CONFS}
timeout --preserve-status -s INT 20s python3 ./scripts/run_renode.py --trace-output ./channel0_0
west zpl-prepare-trace ./channel0_0 -o ./tef_memory_profiling.json

### TVM profiler
west build -p -b $BOARD samples/profiling/tvm_profiler -- ${CTF_CONFS}
timeout --preserve-status -s INT 20s python3 ./scripts/run_renode.py --trace-output ./channel0_0
west zpl-prepare-trace ./channel0_0 \
  --tvm-model-path ./samples/common/tvm/model/magic-wand-graph.json \
  -o ./tef_tvm_profiler.json

### Marking code scopes
west build -p -b $BOARD samples/basic/marking_code_scopes -- ${CTF_CONFS}
timeout --preserve-status -s INT 30s python3 ./scripts/run_renode.py --trace-output ./channel0_0
west zpl-prepare-trace ./channel0_0 -o ./tef_marking_code_scopes.json

### CPU load
west build -p -b $BOARD samples/profiling/cpu_load -- ${CTF_CONFS}
timeout --preserve-status -s INT 20s python3 ./scripts/run_renode.py --trace-output ./channel0_0
west zpl-prepare-trace ./channel0_0 -o ./tef_cpu_load.json
