# Zephelin usage examples

This chapter provides links to relevant resources, application examples and [Trace Viewer](visual_interface) views.

:::{note}
For details on how each demo is executed, open collapsible description of launch example.

Before running commands, make sure you went through [Initializing the workspace](setting-up-workspace) and [Running sample project in Zephelin](running-samples) as it is needed to prepare the environment.
:::

## Using code scopes

* **Source**: {zpl_repo}`samples/basic/marking_code_scopes`
* **Trace Viewer**: [preview](_static/trace_viewer/index.html#profileURL=./tef_marking_code_scopes.json){.external}

This sample demonstrates usage of `ZPL_MARK_CODE_SCOPE` which was described in [Code scopes chapter](code_scopes).

:::::{example} Generating traces for code with scopes defined
:collapsible:

To build a sample run:

```bash
west build -p -b max32690fthr/max32690/m4 samples/basic/marking_code_scopes -- -DCONFIG_ZPL_TRACE_FORMAT_CTF=y -DCONFIG_TRACING_BUFFER_SIZE=10000 -DCONFIG_BOOT_BANNER=n -DCONFIG_PRINTK=n -DCONFIG_LOG=n
```

Secondly, the traces can be either obtained from hardware or Renode simulation with:

::::{tabs}

:::{group-tab} Renode
For Renode, simulation and collection of traces can be done with:

```bash
python3 ./scripts/run_renode.py --trace-output ./trace.ctf --timeout 45
```
:::

:::{group-tab} Hardware
For hardware, once the device is flashed the traces can be collected with:

```bash
west zpl-uart-capture /dev/ttyUSB0 115200 ./trace.ctf
```
:::
::::

Then, the TEF traces can be created with `west zpl-prepare-trace` like so:

```bash
west zpl-prepare-trace ./trace.ctf -o ./tef_marking_code_scopes.json
```

In the end, generated `tef_marking_code_scopes.json` can be loaded in [Trace Viewer](https://antmicro.github.io/zephelin-trace-viewer/).
:::::

## Simple TFLite Micro profiling

* **Source**: {zpl_repo}`samples/profiling/tflm_profiler`
* **Trace Viewer**: [preview](_static/trace_viewer/index.html#profileURL=./tef_tflm_profiler.json){.external}

This sample demonstrates tracing of the TensorFlow Lite Micro (or LiteRT) runtime.
The collection of traces is performed as usual, but in `west zpl-prepare-trace` you need to provide `--tflm-model-path <path-to-model>` flag with used model.

:::::{example} Generating traces for TFLite Micro runtime
:collapsible:

To build a sample run:

```bash
west build -p -b max32690fthr/max32690/m4 samples/profiling/tflm_profiler -- -DCONFIG_ZPL_TRACE_FORMAT_CTF=y -DCONFIG_TRACING_BUFFER_SIZE=10000 -DCONFIG_BOOT_BANNER=n -DCONFIG_PRINTK=n -DCONFIG_LOG=n
```

Secondly, the traces can be either obtained from hardware or Renode simulation with:

::::{tabs}

:::{group-tab} Renode
For Renode, simulation and collection of traces can be done with:

```bash
python3 ./scripts/run_renode.py --trace-output ./trace.ctf --timeout 45
```
:::

:::{group-tab} Hardware
For hardware, once the device is flashed the traces can be collected with:

```bash
west zpl-uart-capture /dev/ttyUSB0 115200 ./trace.ctf
```
:::
::::

Then, the TEF traces can be created with `west zpl-prepare-trace` like so:

```bash
west zpl-prepare-trace ./trace.ctf \
  --tflm-model-path ./samples/common/tflm/model/magic-wand.tflite \
  -o ./tef_tflm_profiler.json
```

In the end, generated `tef_tflm_profiler.json` can be loaded in [Trace Viewer](https://antmicro.github.io/zephelin-trace-viewer/).
:::::

## Simple microTVM profiling

* **Source**: {zpl_repo}`samples/profiling/tvm_profiler`
* **Trace Viewer**: [preview](_static/trace_viewer/index.html#profileURL=./tef_tvm_profiler.json){.external}

This sample demonstrates tracing of the microTVM runtime.
The collection of traces is performed as usual, but in `west zpl-prepare-trace` you need to provide:

* `--tvm-model-path <path-to-model-graph>` - path to JSON with model graph
* `--tvm-model-metadata-path <path-to-metadata>` - path to metadata from compilation results

For more details on above flags check {doc}`ctf_to_tef`.

:::::{example} Generating traces for microTVM runtime
:collapsible:

To build a sample run:

```bash
west build -p -b max32690fthr/max32690/m4 samples/profiling/tflm_profiler -- -DCONFIG_ZPL_TRACE_FORMAT_CTF=y -DCONFIG_TRACING_BUFFER_SIZE=10000 -DCONFIG_BOOT_BANNER=n -DCONFIG_PRINTK=n -DCONFIG_LOG=n
```

Secondly, the traces can be either obtained from hardware or Renode simulation with:

::::{tabs}

:::{group-tab} Renode
For Renode, simulation and collection of traces can be done with:

```bash
python3 ./scripts/run_renode.py --trace-output ./trace.ctf --timeout 45
```
:::

:::{group-tab} Hardware
For hardware, once the device is flashed the traces can be collected with:

```bash
west zpl-uart-capture /dev/ttyUSB0 115200 ./trace.ctf
```
:::
::::

Then, the TEF traces can be created with `west zpl-prepare-trace` like so:

```bash
west zpl-prepare-trace ./trace.ctf \
  --tvm-model-path ./samples/common/tvm/model/magic-wand-graph.json \
  --tvm-model-metadata-path ./samples/common/tvm/model/magic-wand-metadata.json \
  -o ./tef_tvm_profiler.json
```

In the end, generated `tef_tvm_profiler.json` can be loaded in [Trace Viewer](https://antmicro.github.io/zephelin-trace-viewer/).
:::::

## Full TFLite Micro traces with instrumentation

* **Source**: {zpl_repo}`samples/profiling/tflm_instrumentation`
* **Trace Viewer**: [preview](_static/trace_viewer/index.html#profileURL=./tef_tflm_instrumentation.json){.external}

This sample demonstrates combining Zephelin tracing with enabled instrumentation and additional metrics.

The collection of traces is performed using `west zpl-instrumentation-uart-gdb-capture` which collects:

* Instrumentation data using UART
* Zephelin data using GDB backend

In this scenario you need to provide instrumentation traces separately using `-i` flag.

Check {doc}`ctf_to_tef` for more details.

:::::{example} Collecting regular and instrumentation traces
:collapsible:

To build a sample run:

```bash
west build -p -b max32690fthr/max32690/m4 samples/profiling/tflm_instrumentation -- -DEXTRA_CONF_FILE="dump_on_full.conf;zpl.conf"
```

Secondly, flash the device or run a simulation and collect traces:

::::{tabs}

:::{group-tab} Renode
For Renode, simulation and collection of traces can be done with:

```bash
python3 ./scripts/run_renode.py --simulation-only --debug
```

This can run in a separate shell, since traces in this case will be obtained separately with a following command:

```bash
west zpl-instrumentation-uart-gdb-capture /tmp/uart-log 115200 ./renode_tflm.instr.ctf ./renode_tflm.gdb.ctf --no-debug-server --timeout 20
```
:::

:::{group-tab} Hardware
For hardware, flash the device and make sure that UART and debug adapter is connected.

Once this is done, run collection of traces with:

```bash
west zpl-instrumentation-uart-gdb-capture /dev/ttyUSB0 115200 ./renode_tflm.instr.ctf ./renode_tflm.gdb.ctf --timeout 20
```

Remember that `/dev/ttyUSB0` may need to be replaced with a different device.
:::
::::

Then, the TEF traces can be created with `west zpl-prepare-trace` like so:

```bash
west zpl-prepare-trace -o tef_tflm_instrumentation.json -i renode_tflm.instr_0.ctf renode_tflm.gdb.ctf --tflm-model-path ./samples/common/tflm/model/sine.tflite --trim-metadata
```

In the end, generated `tef_tflm_instrumentation.json` can be loaded in [Trace Viewer](https://antmicro.github.io/zephelin-trace-viewer/).
:::::

## Multithreaded application running multiple models

* **Source**: {zpl_repo}`samples/profiling/smp_tvm`
* **Trace Viewer**: [preview](_static/trace_viewer/index.html#profileURL=./tef_smp_tvm_models.json){.external} (models are running on a different thread than `main`)

Zephelin allows tracing of applications running on multiple threads and cores with no additional configuration changes.
Each event contains ID of the CPU which emitted it and this ID is used during parsing traces.

This sample loads four simple models using TVM runtime.
Those models are then executed on different CPUs using random input data generated by main thread.

:::::{example} Tracing multiple threads with Zephelin
:collapsible:

To build a sample run:
```bash
west build -p -b  mpfs_icicle/polarfire/u54/smp samples/profiling/smp_tvm
```

:::{note}
The `mpfs_icicle/polarfire/u54/smp` is used to demonstrate the work on several cores.
:::

The above sample can be executed on hardware or simulated in Renode with:

```bash
python ./scripts/run_renode.py --trace-output ./smp.ctf
```

Finally, to parse produced `./smp.ctf` run:

```bash
west zpl-prepare-trace ./smp.ctf -o ./tef_smp_tvm_models.json \
  --tvm-model-paths ./samples/common/tvm/model/sine-graph.json \
    ./samples/common/tvm/model/magic-wand-graph.json \
  --tvm-model-metadata-paths ./samples/common/tvm/model/sine-metadata.json \
    ./samples/common/tvm/model/magic-wand-metadata.json \
  --tvm-model-op-remove-prefix 'tvmgen_[a-zA-Z0-9]+_fused_' \
  --trim-metadata
```

In the Trace Viewer there should be separate thread for each model and each of those threads should contain events produced by that model.
:::::
