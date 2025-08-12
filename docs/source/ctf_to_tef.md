# CTF to TEF conversion

In order to expand the compatibility of received trace in Common Trace Format (CTF), we had prepared a converter to the [Trace Event Format](https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/edit?tab=t.0#heading=h.yr4qxyxotyw) (TEF).

## Requirements

The converter is a Python script requiring few dependencies:
* [Babeltrace](https://github.com/efficios/babeltrace) with Python bindings
* [PyYAML](https://github.com/yaml/pyyaml)
* [LiteRT](https://github.com/google-ai-edge/LiteRT) - only for extracting metadata from LiteRT models, can be installed with `pip3 install ai-edge-litert`

## Usage

The converter can be used with a following command:

```bash
west zpl-prepare-trace \
  [-h] -o OUTPUT [--zephyr-base ZEPHYR_BASE] [--build-dir BUILD_DIR] \
  [--tflm-model-path TFLM_MODEL_PATH] [--tvm-model-path TVM_MODEL_PATH] \
  ctf_trace
```

There are a few optional arguments:
* `--zephyr-base` - the script tries to automatically find the Zephyr directory in order to use metadata file definition of CTF events, if this cannot done, user has to provide the path or set `ZEPHYR_BASE` environmental variable,
* `--build-dir` - the directory storing results of build and [ram_report](https://docs.zephyrproject.org/latest/develop/optimizations/tools.html#build-target-ram-report).
* `--tflm-model-path` - the given TFLite Micro model is processed to extract information about its layer and tensors, the information is converted to [`MODEL`](model-event) {{TEF_Metadata}} event,
* `--tvm-model-path` - the given microTVM graph JSON file is processed to extract information about model's layer and tensors, the information is converted to [`MODEL`](model-event) {{TEF_Metadata}} Event,
* `-o` - points to the file where the converted trace should be saved, if not provided the JSON will be printed to STDOUT.

It, apart from changing format, implements custom logic which can group elements into {{TEF_Duration}} events and extend their arguments (see [](converted-events)).
Moreover, a completely new events can be added to the trace extending the context and improving the trace visualization capabilities (see [](optional-events)).
Furthermore, the command also converts timestamps from nanoseconds (used in CTF) to microseconds, as Speedscope assumes they are provided in such unit.

## Events

(converted-events)=
### Converted events

This section contains events that are not produced during the Zeppelin runtime, but are used to provide additional information for a better visualizations.

#### Zephyr events

For default Zephyr events (defined in [metadata](https://github.com/zephyrproject-rtos/zephyr/blob/main/subsys/tracing/ctf/tsdl/metadata)), the beginning event has always the `_enter` suffix, whereas the end event has `_exit`.
These events are marked as `B` and `E` events, creating {{TEF_Duration}} event in TEF.
The remaining Zephyr events are of {{TEF_Instant}} type, but as Speedscope does not support displaying such events, they are also converted to the Duration Event with 1 microsecond of duration.

:::{admonition} Example event
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

The {{TEF_Duration}} event marking the beginning and end of the inference.
It is created from `zpl_inference_enter` and `zpl_inference_exit` CTF events.

:::{admonition} Example event
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

The `MODEL::*` {{TEF_Duration}} event is unique for each layer of model, described with:
* `LAYER_OP` - a tag of operation like `CONV_2D` or `MAX_POOL_2D`,
* `SUBGRAPH_IDX` - an optional number representing the ID of subgraph to which a given layer belongs,
* `OP_IDX` - a number representing the ID of the operation in a subgraph.

The event contains:
* identifiers like `op_idx` and optional `subgraph_idx`,
* `tag` with layer name,
* `thread_id` pointing to the thread that executed this layer,
* `runtime` specifying which runtime was used,
* and additional runtime-specific data.

This event is converted from TFLite micro (`zpl_tflm_(enter|exit)`) and microTVM (`zpl_tvm_(enter|exit)`) events.

:::{admonition} Example event
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

The {{TEF_Metadata}} event with information about a [memory region](memory-ctf) in a given timestamp (`ts`).
It is created from `zpl_memory` CTF event.

:::{admonition} Example event
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

#### `CPU_LOAD`

The {{TEF_Metadata}} event defining CPU load (`cpu_load` field) in a given timestamp (`ts`).
It is converted from `zpl_cpu_load_event` CTF event.

:::{admonition} Example event
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

#### `DIE_TEMP`

The {{TEF_Metadata}} event providing DIE temperatures (`die_temp` array with at most two measurements in degrees Celsius) for a given timestamp (`ts`).
It is converted from `zpl_die_temp_event` CTF event.

:::{admonition} Example event
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

This section contains events that are not produced during the Zeppelin runtime, but are used to provide additional information for a better visualizations.

(memory-statically-assigned-mem-event)=
#### `MEMORY::STATICALLY_ASSIGNED_MEM`

The {{TEF_Metadata}} event informing about the part of RAM (in bytes), used by the compiled objects.
This value is calculated using size from [ram_report](https://docs.zephyrproject.org/latest/develop/optimizations/tools.html#build-target-ram-report) and subtracting sizes of the memory regions (from [`MEMORY` events](memory-event)).
The event looks like:

:::{admonition} Example event
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

The {{TEF_Metadata}} event containing mapping of memory region addresses to their symbols extracted from `zephyr.elf`.
It is used to present human-readable description of the regions, e.g. making it easier to trace back to source code.
The example event:

:::{admonition} Example event
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

The {{TEF_Metadata}} event used by Speedscope to associate thread ID with a name.
Apart from describing which thread is shown on the flamegraph, the thread name is also used to provide human-readable label for the thread stack.

The one event describes exactly one thread with arguments containing thread name assigned to the key `name`.

:::{admonition} Example event
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
* `inputs` - specification of model inputs, described with `name`, `shape` and `dtype`,
* `outputs` - specification of model outputs, with the same properties as `inputs`,
* `tensors` - specification of internal data like inputs and outputs of layers, their weights or biases; the properties are the same as `inputs` with additional `index` and optional `subgraph_idx`,
* `ops` - specification of model operations:
  * `op_name` - name of the operation (e.g. `CONV_2D` or `tvmgen_default_fused_nn_conv2d_add_nn_relu`),
  * `index` - ID of the operation,
  * `inputs` and `outputs` - list of `index`es pointing to elements from `tensors` which specify operation's inputs and outputs properties,
  * `inputs_types` and `outputs_types` - operation's inputs and outputs data types,
  * `inputs_shapes` and `outputs_shapes` - operation's inputs and outputs shapes.

:::{admonition} Example event of MagicWand model for TFLite micro runtime
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
