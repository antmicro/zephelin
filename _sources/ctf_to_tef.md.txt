# CTF to TEF conversion

In order to expand the compatibility of the traces received in Common Trace Format (CTF), we created a converter for obtaining them in the [Trace Event Format (TEF)](https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/edit?tab=t.0#heading=h.yr4qxyxotyw).

## Usage

You can run the converter with the following command:

```bash
west zpl-prepare-trace \
  [-h] -o OUTPUT [--zephyr-base ZEPHYR_BASE] [--build-dir BUILD_DIR] \
  [--tflm-model-path TFLM_MODEL_PATH] [--tvm-model-path TVM_MODEL_PATH] \
  [--instrumentation-ctf INSTRUMENTATION_CTF] \
  ctf_trace
```

There are several optional arguments available:
* `--zephyr-base` - the script tries to automatically find the Zephyr directory in order to use the metadata file definition of CTF events.
  If this fails, you have to provide the path or set the `ZEPHYR_BASE` environmental variable.
* `--build-dir` - the directory storing the results of the build and [ram_report](https://docs.zephyrproject.org/latest/develop/optimizations/tools.html#build-target-ram-report).
* `--tflm-model-path` - the provided TFLite Micro model is processed to extract information about its layer and tensors, and the information is converted to [`MODEL`](model-event) {{TEF_Metadata}} event.
* `--tvm-model-path` - the provided microTVM graph JSON file is processed to extract information about model's layer and tensors, and the information is converted to [`MODEL`](model-event) {{TEF_Metadata}} Event,
* `--instrumentation-ctf` - the separate CTF file, containing instrumentation traces.
* `-o` - the file path which points to the file where the converted trace should be saved.
  If not provided, the JSON will be printed to STDOUT.

Apart from changing the format, this involves a custom logic which can group elements into {{TEF_Duration}} events, and extend their arguments (see [](converted-events)).
Completely new events can be added to the trace, extending the context, and improving the trace visualization capabilities (see [](optional-events)).
Furthermore, the command also converts timestamps from nanoseconds (used in CTF) to microseconds, which are valid for Zephelin Trace Viewer and Speedscope (it assumes that the timestamps are provided in such unit).

## Events

(converted-events)=
### Converted events

This section describes events that are converted from CTF events, emitted during Zephelin runtime.
Based on those, the trace viewer produces dedicated panels with visualizations (e.g. plot panels).

#### Zephyr events

For default Zephyr events (defined in [metadata](https://github.com/zephyrproject-rtos/zephyr/blob/main/subsys/tracing/ctf/tsdl/metadata)), the beginning event always gets the `_enter` suffix, whereas the ending event gets the `_exit` suffix.
These events are marked as `B` and `E` events, creating {{TEF_Duration}} event in TEF.
The remaining Zephyr events are of {{TEF_Instant}} type, but since Speedscope does not support displaying such events, they are also converted to a Duration Event with 1 microsecond of duration.

:::{example} Example events
:collapsible:
```json
{
  "name": "isr",
  "cat": "zephyr",
  "ph": "B",
  "ts": 99967.43400000001,
  "pid": 0,
  "tid": 0
},
"...",
{
  "name": "isr",
  "cat": "zephyr",
  "ph": "E",
  "ts": 99980.142,
  "pid": 0,
  "tid": 0
}
```
:::

#### `zpl_inference`

The {{TEF_Duration}} event marking the beginning and end of model's inference.
It is created from the CTF events `zpl_inference_enter` and `zpl_inference_exit`.

:::{example} `zpl_inference` events examples
:collapsible:
```json
{
  "name": "zpl_inference",
  "cat": "zephyr",
  "ph": "B",
  "ts": 0.0,
  "pid": 0,
  "tid": 536912424,
  "args": {
    "thread_id": 536912424
  }
},
"...",
{
  "name": "zpl_inference",
  "cat": "zephyr",
  "ph": "E",
  "ts": 110497.391,
  "pid": 0,
  "tid": 536912424,
  "args": {
    "thread_id": 536912424
  }
}
```
:::

#### `MODEL::{LAYER_OP}[_{SUBGRAPH_IDX}]_{OP_IDX}`

The `MODEL::*` {{TEF_Duration}} event is unique to each layer of a model, described with:
* `LAYER_OP` - a tag of operation like `CONV_2D` or `MAX_POOL_2D`,
* `SUBGRAPH_IDX` - an optional number representing the ID of a subgraph to which a given layer belongs,
* `OP_IDX` - a number representing the ID of the operation in a subgraph.

The event contains:
* identifiers like `op_idx` and optional `subgraph_idx`,
* `tag` with the layer name,
* `thread_id` pointing to the thread that executed this layer,
* `runtime` specifying which runtime was used, and
* additional runtime-specific data.

This event is converted from TFLite micro (`zpl_tflm_(enter|exit)`) and microTVM (`zpl_tvm_(enter|exit)`) events.

:::{example} `MODEL::*` events examples
:collapsible:
```json
{
  "name": "MODEL::CONV_2D_0_0",
  "cat": "zephyr",
  "ph": "B",
  "ts": 4294973.212,
  "pid": 0,
  "tid": 536912424,
  "args": {
    "thread_id": 536912424,
    "subgraph_idx": 0,
    "op_idx": 0,
    "tag": "CONV_2D",
    "arena_used_bytes": 15408,
    "arena_tail_usage": 88,
    "runtime": "TFLite Micro"
  }
},
{
  "name": "MODEL::CONV_2D_0_0",
  "cat": "zephyr",
  "ph": "E",
  "ts": 4359202.146,
  "pid": 0,
  "tid": 536912424,
  "args": {
    "thread_id": 536912424,
    "subgraph_idx": 0,
    "op_idx": 0,
    "tag": "CONV_2D",
    "arena_used_bytes": 15408,
    "arena_tail_usage": 88,
    "runtime": "TFLite Micro"
  }
}
```
:::

(memory-event)=
#### `MEMORY`

The {{TEF_Metadata}} event with information about a [memory region](memory-ctf) for a given timestamp (`ts`).
It is created from the CTF event `zpl_memory`.

:::{example} `MEMORY` metadata example
:collapsible:
```json
{
  "name": "MEMORY",
  "cat": "zephyr",
  "ph": "M",
  "ts": 55.216,
  "pid": 0,
  "tid": 536937200,
  "args": {
    "memory_region": "STACK",
    "memory_addr": 536950376,
    "used": 88,
    "unused": 424,
    "for_thread_id": 536936848
  }
}
```
:::

(cpu-load-event)=
#### `CPU_LOAD`

The {{TEF_Metadata}} event defining CPU load (`cpu_load` field) for a given timestamp (`ts`).
It is converted from the CTF event `zpl_cpu_load_event`.

:::{example} `CPU_LOAD` metadata example
:collapsible:
```json
{
  "name": "CPU_LOAD",
  "cat": "zephyr",
  "ph": "M",
  "ts": 200044.308,
  "pid": 0,
  "tid": 0,
  "args": {
    "cpu_load": 534
  }
}
```
:::

(die-temp-event)=
#### `DIE_TEMP`

The {{TEF_Metadata}} event providing DIE temperatures (`die_temp` array with at most two measurements, in degrees Celsius) for a given timestamp (`ts`).
It is converted from the CTF event `zpl_die_temp_event`.

:::{example} `DIE_TEMP` metadata example
:collapsible:
```json
{
  "name": "DIE_TEMP",
  "cat": "zephyr",
  "ph": "M",
  "ts": 300327.025,
  "pid": 0,
  "tid": 0,
  "args": {
    "die_temp": [
      21.947092056274414,
      41.94709014892578
    ]
  }
}
```
:::

(optional-events)=
### Additional events

This section contains events that are not produced during the Zephelin runtime, but are used to provide additional information for better visualizations.

(memory-statically-assigned-mem-event)=
#### `MEMORY::STATICALLY_ASSIGNED_MEM`

The {{TEF_Metadata}} event informing about the part of RAM (in bytes), used by the compiled objects.
This value is calculated using size from [ram_report](https://docs.zephyrproject.org/latest/develop/optimizations/tools.html#build-target-ram-report) and subtracting sizes of the memory regions (from [`MEMORY` events](memory-event)).
The event looks like this:

:::{example} `MEMORY::STATICALLY_ASSIGNED_MEM` metadata example
:collapsible:
```json
{
  "name": "MEMORY::STATICALLY_ASSIGNED_MEM",
  "cat": "zephyr",
  "ph": "M",
  "pid": 0,
  "tid": 0,
  "ts": 0,
  "args": 14105
}
```
:::

(memory-symbols-event)=
#### `MEMORY::SYMBOLS`

The {{TEF_Metadata}} event contains the mapping of memory region addresses to their symbols extracted from `zephyr.elf`.
It is used to present human-readable description of the regions, e.g. making it easier to trace back to the source code.
Example event:

:::{example} `MEMORY::SYMBOLS` metadata example
:collapsible:
```json
{
  "name": "MEMORY::SYMBOLS",
  "cat": "zephyr",
  "ph": "M",
  "pid": 0,
  "tid": 0,
  "ts": 0,
  "args": {
    "536950376": "_k_thread_stack_zpl_mem_profiling",
    "536949352": "tracing_thread_stack",
    "536952936": "z_idle_stacks",
    "536953256": "z_main_stack",
    "536938172": "z_malloc_heap",
    "536936540": "_system_heap",
    "536936560": "test_k_heap",
    "536936512": "test_mem_slab"
  }
}
```
:::

#### `thread_name`

The {{TEF_Metadata}} event is used by Speedscope to associate a thread ID with a name.
Apart from describing which thread is shown on the flamegraph, the thread name is also used to provide human-readable label for the thread stack.

One event describes exactly one thread with arguments containing the thread name, assigned to the key `name`.

:::{example} `thread_name` metadata example
:collapsible:
```json
{
  "name": "thread_name",
  "cat": "zephyr",
  "ph": "M",
  "pid": 0,
  "tid": 536912424,
  "args": {
    "name": "main"
  }
}
```
:::

(model-event)=
#### `MODEL`

The `MODEL` {{TEF_Metadata}} event contains following information:
* `inputs` - the specification of model inputs, described with `name`, `shape` and `dtype`,
* `outputs` - the specification of model outputs, with the same properties as `inputs`,
* `tensors` - the specification of internal data like inputs and outputs of layers, their weights or biases; the properties are the same as `inputs`, but with additional `index` and optional `subgraph_idx`,
* `ops` - the specification of model operations:
  * `op_name` - the name of the operation (e.g. `CONV_2D` or `tvmgen_default_fused_nn_conv2d_add_nn_relu`),
  * `index` - the ID of the operation,
  * `inputs` and `outputs` - lists with indices pointing to `tensors` with input and output data (respectively),
  * `inputs_types` and `outputs_types` - the operation's input and output data types,
  * `inputs_shapes` and `outputs_shapes` - the operation's input and output shapes.

:::{example} Example event of Magic Wand model for TFLite Micro runtime
:collapsible:
```json
{
  "name": "MODEL",
  "cat": "zephyr",
  "ph": "M",
  "pid": 0,
  "tid": 0,
  "ts": 0,
  "args": {
    "inputs": [
      {
        "name": "input_1",
        "name_long": "serving_default_input_1:0",
        "shape": [1, 128, 3, 1],
        "shape_signature": [-1, 128, 3, 1],
        "dtype": "float32",
        "quantization": [0.0, 0],
        "quantization_parameters": {
          "scales": [],
          "zero_points": [],
          "quantized_dimension": 0
        }
      }
    ],
    "outputs": [
      {
        "name": "out_layer",
        "name_long": "StatefulPartitionedCall:0",
        "shape": [1, 4],
        "shape_signature": [-1, 4],
        "dtype": "float32",
        "quantization": [0.0, 0],
        "quantization_parameters": {
          "scales": [],
          "zero_points": [],
          "quantized_dimension": 0
        }
      }
    ],
    "tensors": [
      {
        "name": "serving_default_input_1:0",
        "subgraph_idx": 0,
        "index": 0,
        "shape": [1, 128, 3, 1],
        "shape_signature": [-1, 128, 3, 1],
        "dtype": "float32",
        "quantization": [0.0, 0],
        "quantization_parameters": {
          "scales": [],
          "zero_points": [],
          "quantized_dimension": 0
        }
      },
      "..."
    ],
    "ops": [
      {
        "op_name": "CONV_2D",
        "index": 0,
        "inputs": [0, 3, 1],
        "outputs": [10],
        "inputs_types": ["float32", "float32", "float32"],
        "outputs_types": ["float32"],
        "inputs_shapes": {
          "0": [1, 128, 3, 1],
          "3": [8, 4, 3, 1],
          "1": [8]
        },
        "outputs_shapes": {
          "10": [1, 128, 3, 8]
        }
      },
      "..."
    ]
  }
}
```
:::
