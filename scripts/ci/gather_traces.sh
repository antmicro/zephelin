#!/bin/bash

# Copyright (c) 2025-2026 Analog Devices, Inc.
# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

set -xeuo pipefail

BOARD=${BOARD:-max32690fthr/max32690/m4}
CTF_CONFS=${CTF_CONFS:-"-DCONFIG_ZPL_TRACE_FORMAT_CTF=y -DCONFIG_TRACING_BUFFER_SIZE=10000 -DCONFIG_BOOT_BANNER=n -DCONFIG_PRINTK=n -DCONFIG_LOG=n"}


### TFLM profiler
west build -p -b $BOARD samples/profiling/tflm_profiler -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./tflm_profiler.ctf --timeout 45
west zpl-prepare-trace ./tflm_profiler.ctf \
  --tflm-model-path ./samples/common/tflm/model/magic-wand.tflite \
  -o ./tef_tflm_profiler.json

### Memory profiling
west build -p -b $BOARD samples/profiling/memory_profiling -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./memory_profiling.ctf --timeout 45
west zpl-prepare-trace ./memory_profiling.ctf -o ./tef_memory_profiling.json

### TVM profiler
west build -p -b $BOARD samples/profiling/tvm_profiler -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./tvm_profiler.ctf --timeout 45
west zpl-prepare-trace ./tvm_profiler.ctf \
  --tvm-model-path ./samples/common/tvm/model/magic-wand-graph.json \
  --tvm-model-metadata-path ./samples/common/tvm/model/magic-wand-metadata.json \
  -o ./tef_tvm_profiler.json

### Marking code scopes
west build -p -b $BOARD samples/basic/marking_code_scopes -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./marking_code_scopes.ctf --timeout 45
west zpl-prepare-trace ./marking_code_scopes.ctf -o ./tef_marking_code_scopes.json

### CPU load
west build -p -b $BOARD samples/profiling/cpu_load -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./cpu_load.ctf --timeout 45
west zpl-prepare-trace ./cpu_load.ctf -o ./tef_cpu_load.json

### TFLM multi model
west build -p -b $BOARD samples/profiling/tflm_multi_model -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./tflm_multi_model.ctf --timeout 45
west zpl-prepare-trace ./tflm_multi_model.ctf -o ./tef_tflm_multi_model.json \
  --tflm-model-paths ./samples/common/tflm/model/magic-wand.tflite \
    ./samples/common/tflm/model/sine.tflite

### TVM multi model
west build -p -b $BOARD samples/profiling/tvm_multi_model -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./tvm_multi_model.ctf --timeout 45
west zpl-prepare-trace ./tvm_multi_model.ctf -o ./tef_tvm_multi_model.json \
  --tvm-model-op-remove-prefix 'tvmgen_[a-zA-Z0-9]+_fused_' \
  --tvm-model-paths ./samples/common/tvm/model/magic-wand-graph.json \
    ./samples/common/tvm/model/sine-graph.json \
  --tvm-model-metadata-paths ./samples/common/tvm/model/magic-wand-metadata.json \
    ./samples/common/tvm/model/sine-metadata.json

### TFLM and TVM models
west build -p -b $BOARD samples/profiling/tflm_tvm_models -- ${CTF_CONFS}
python3 ./scripts/run_renode.py --trace-output ./tflm_tvm_models.ctf --timeout 45
west zpl-prepare-trace ./tflm_tvm_models.ctf -o ./tef_tflm_tvm_models.json \
  --tflm-model-paths ./samples/common/tflm/model/sine.tflite \
  --tvm-model-paths ./samples/common/tvm/model/sine-graph.json \
    ./samples/common/tvm/model/sine2-graph.json \
  --tvm-model-metadata-paths ./samples/common/tvm/model/sine-metadata.json \
    ./samples/common/tvm/model/sine2-metadata.json \
  --tvm-model-op-remove-prefix 'tvmgen_[a-zA-Z0-9]+_fused_' \
  --trim-metadata

### SMP TVM sample
west build -p -b  mpfs_icicle/polarfire/u54/smp samples/profiling/smp_tvm
python3 ./scripts/run_renode.py --trace-output ./smp_tvm.ctf --timeout 45
west zpl-prepare-trace ./smp_tvm.ctf -o ./tef_smp_tvm_models.json \
  --tvm-model-paths ./samples/common/tvm/model/sine-graph.json \
    ./samples/common/tvm/model/magic-wand-graph.json \
  --tvm-model-metadata-paths ./samples/common/tvm/model/sine-metadata.json \
    ./samples/common/tvm/model/magic-wand-metadata.json \
  --tvm-model-op-remove-prefix 'tvmgen_[a-zA-Z0-9]+_fused_' \
  --trim-metadata

# TFLM instrumentation with ZPL events
west build -p -b $BOARD samples/profiling/tflm_instrumentation -- -DEXTRA_CONF_FILE="dump_on_full.conf;zpl.conf"
python3 ./scripts/run_renode.py --simulation-only \
  --debug --renode-logs &> run_renode_tflm_instrumentation.log &
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
  --debug --debug-start-immediately --renode-logs &> run_renode_tvm_instrumentation.log &
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

# SMP TVM sample with GDB capture
west build -p -b  mpfs_icicle/polarfire/u54/smp samples/profiling/smp_tvm -- \
  -DCONFIG_ZPL_TRACE_BACKEND_DEBUGGER=y -DCONFIG_ZPL_TRACE_FORMAT_CTF=y
python3 ./scripts/run_renode.py --simulation-only \
  --debug --renode-logs &> run_renode_tflm_gdb.log &
RENODE_SIM=$!
sleep 5
timeout --preserve-status -s INT 1m west zpl-gdb-capture --no-debug-server ./smp_tvm_gdb.ctf
kill $RENODE_SIM && rm /tmp/uart-log
west zpl-prepare-trace ./smp_tvm_gdb.ctf -o ./tef_smp_tvm_gdb.json \
  --tvm-model-paths ./samples/common/tvm/model/sine-graph.json \
    ./samples/common/tvm/model/magic-wand-graph.json \
  --tvm-model-metadata-paths ./samples/common/tvm/model/sine-metadata.json \
    ./samples/common/tvm/model/magic-wand-metadata.json \
  --tvm-model-op-remove-prefix 'tvmgen_[a-zA-Z0-9]+_fused_' \
  --trim-metadata

# Two TFLM models with external clock
west build -p -b max32650fthr --sysbuild samples/multi_machine/two_models/node_0 -- \
   -Dnode_0_CONFIG_ZPL_TRACE_FORMAT_CTF=y \
   -Dnode_0_CONFIG_TRACING_BUFFER_SIZE=10000 \
   -Dnode_1_CONFIG_ZPL_TRACE_FORMAT_CTF=y \
   -Dnode_1_CONFIG_TRACING_BUFFER_SIZE=10000
python3 ./scripts/run_renode_multimachine.py \
	--boards max32650fthr max32650fthr \
	--elfs build/node_0/zephyr/zephyr.elf build/node_1/zephyr/zephyr.elf \
	--trace_uarts uart0 uart0 \
	--shared-clock-address 0x400FFFF0 \
	--offset 2000 \
	--trace-output ./trace.ctf \
	--timeout 20
west zpl-prepare-trace ./trace.ctf \
  --build-dir build/node_0 \
  --tflm-model-path ./samples/common/tflm/model/magic-wand.tflite \
  --zephyr-elf-path build/node_0/zephyr/zephyr.elf \
  -o ./tef_tflm_profiler_0.json
west zpl-prepare-trace ./trace_1.ctf \
  --build-dir build/node_1 \
  --tflm-model-path ./samples/common/tflm/model/magic-wand.tflite \
  --zephyr-elf-path build/node_1/zephyr/zephyr.elf \
  -o ./tef_tflm_profiler_1.json

# Two TFLM models comunicating
west build -p -b max32650evkit -d build_preprocessor samples/multi_machine/micro_speech/preprocessor -- ${CTF_CONFS}
west build -p -b max32650evkit -d build_micro_speech samples/multi_machine/micro_speech/micro_speech -- ${CTF_CONFS}

python3 ./scripts/run_renode_multimachine.py \
--boards max32650evkit max32650evkit \
--elfs build_preprocessor/zephyr/zephyr.elf build_micro_speech/zephyr/zephyr.elf \
--repls samples/multi_machine/micro_speech/boards/max32650evkit.repl samples/multi_machine/micro_speech/boards/max32650evkit.repl \
--trace_uarts uart0 uart0 \
--uart-connect uart1 \
--shared-clock-address 0x400FFFF0 \
--trace-output micro_speech.ctf \
--timeout 45

west zpl-prepare-trace ./micro_speech.ctf \
  --build-dir build/micro_speech \
  --tflm-model-path ./samples/common/tflm/model/micro_speech_quantized.tflite \
  -o ./tef_micro_speech.json \
  --zephyr-elf-path build/micro_speech/zephyr/zephyr.elf

west zpl-prepare-trace ./micro_speech_1.ctf \
  --build-dir build/preprocessor \
  --tflm-model-path ./samples/common/tflm/model/audio_preprocessor_int8.tflite \
  -o ./tef_preprocessor.json \
  --zephyr-elf-path build/preprocessor/zephyr/zephyr.elf

# Validate generated CTFs
if [[ $(ls -l -s *.ctf | awk '($6 > 0)' | wc -l) -lt 18 ]]; then
  echo "Wrong number of non-zero CTF files" 1>&2
  exit 1
fi
