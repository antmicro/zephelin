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
  --tvm-model-op-remove-prefix 'tvmgen_[a-zA-Z0-9]+_fused_' \
  --tvm-model-paths ./samples/common/tvm/model/magic-wand-graph.json \
    ./samples/common/tvm/model/sine-graph.json \
  --tvm-model-metadata-paths ./samples/common/tvm/model/magic-wand-metadata.json \
    ./samples/common/tvm/model/sine-metadata.json

### TFLM and TVM models
west build -p -b $BOARD samples/profiling/tflm_tvm_models -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./channel0_0 --timeout 45
west zpl-prepare-trace ./channel0_0 -o ./tef_tflm_tvm_models.json \
  --tflm-model-paths ./samples/common/tflm/model/sine.tflite \
  --tvm-model-paths ./samples/common/tvm/model/sine-graph.json \
    ./samples/common/tvm/model/sine2-graph.json \
  --tvm-model-metadata-paths ./samples/common/tvm/model/sine-metadata.json \
    ./samples/common/tvm/model/sine2-metadata.json \
  --tvm-model-op-remove-prefix 'tvmgen_[a-zA-Z0-9]+_fused_' \
  --trim-metadata

### SMP TVM sample
west build -p -b  mpfs_icicle/polarfire/u54/smp samples/profiling/smp_tvm
python3 ./scripts/run_renode.py --trace-output ./channel0_0 --timeout 45
west zpl-prepare-trace ./channel0_0 -o ./tef_smp_tvm_models.json \
  --tvm-model-paths ./samples/common/tvm/model/sine-graph.json \
    ./samples/common/tvm/model/magic-wand-graph.json \
  --tvm-model-metadata-paths ./samples/common/tvm/model/sine-metadata.json \
    ./samples/common/tvm/model/magic-wand-metadata.json \
  --tvm-model-op-remove-prefix 'tvmgen_[a-zA-Z0-9]+_fused_' \
  --trim-metadata

# TFLM instrumentation with ZPL events
west build -p -b $BOARD samples/profiling/tflm_instrumentation -- -DEXTRA_CONF_FILE="dump_on_full.conf;zpl.conf"
python3 ./scripts/run_renode.py --simulation-only \
  --debug &> run_renode_tflm_instrumentation.log &
RENODE_SIM=$!
sleep 5
west zpl-instrumentation-uart-gdb-capture \
  /tmp/uart-log 115200 ./renode_tflm.instr.ctf ./renode_tflm.gdb.ctf \
  --no-debug-server --timeout 20
kill $RENODE_SIM && rm /tmp/uart-log
west zpl-prepare-trace -o tef_tflm_instrumentation.json -i renode_tflm.instr_0.ctf renode_tflm.gdb.ctf \
  --tflm-model-path ./samples/common/tflm/model/sine.tflite --trim-metadata

# TVM instrumentation with ZPL events
west build -p -b $BOARD samples/profiling/tvm_instrumentation -- -DEXTRA_CONF_FILE=zpl.conf
python3 ./scripts/run_renode.py --simulation-only \
  --debug --debug-start-immediately &> run_renode_tvm_instrumentation.log &
RENODE_SIM=$!
sleep 5
west zpl-instrumentation-uart-gdb-capture \
  /tmp/uart-log 115200 ./renode_tvm.instr.ctf ./renode_tvm.gdb.ctf \
  --no-debug-server --n-bytes 1000
kill $RENODE_SIM && rm /tmp/uart-log
west zpl-prepare-trace -o tef_tvm_instrumentation.json -i renode_tvm.instr.ctf renode_tvm.gdb.ctf \
  --tvm-model-path ./samples/common/tvm/model/sine-graph.json \
  --tvm-model-metadata ./samples/common/tvm/model/sine-metadata.json \
  --tvm-model-op-remove-prefix 'tvmgen_[a-zA-Z0-9]*_fused_' \
  --trim-metadata
