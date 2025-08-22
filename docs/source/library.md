# Zeppelin project

Zeppelin is implemented as a West module.
The Zeppelin repository consists of the following elements:

* Zeppelin library
* Custom configurations of boards based on MAX78002 and MAX32690 - for testing purposes
* Sample applications, which also serve as integration tests
* Unit tests
* Patches to Zephyr RTOS

## Initializing the workspace

First, make sure all dependencies required by [Zephyr RTOS](https://www.zephyrproject.org/) are installed - follow the [Getting started guide](https://docs.zephyrproject.org/latest/develop/getting_started/index.html).

Secondly, create a workspace and clone the Zeppelin repository:

```bash
mkdir workspace && cd workspace
git clone --recursive git@github.com:antmicro/zeppelin.git
cd zeppelin
```

Then, install `west` and additional dependencies listed in project's `requirements.txt` with `pip`:

```bash
pip install -r requirements.txt
```

Next, initialize the workspace using West. To do that, run the following command:

```bash
west init -l .
```

Download, patch and prepare the project sources using the following commands:

```
west update
west patch apply
west zephyr-export
west packages pip --install
```

For testing without hardware in the loop, download Renode portable and add the download path to `PATH` environment variable:

```bash
wget https://builds.renode.io/renode-latest.linux-portable-dotnet.tar.gz
mkdir renode-portable
tar --strip-components=1 -C ./renode-portable -xvf renode-latest.linux-portable-dotnet.tar.gz
export PATH=$(pwd)/renode-portable:$PATH
```

Finally, download Zephyr SDK:

```bash
west sdk install
```

## Running a sample project with Zeppelin

To collect traces and visualize them using Zeppelin Trace Viewer, you can run [a simple demo with gesture recognition](./samples/demo), based on the data from an accelerometer in a Renode simulation.
The default [configuration](./samples/demo/prj.conf) in this demo collects traces along with all possibile additional information, like memory usage, die temperature, inference statistics, and more.
One UART provides logs from the application, whereas the other UART returns CTF traces.

To build the demo, run:

```bash
west build -p -b stm32f746g_disco/stm32f746xx samples/demo
```

To run it in a Renode simulation, run:

```bash
python ./scripts/run_renode.py \
    --repl ./samples/demo/boards/stm32f746g_disco_lis2ds12.repl \
    --sensor i2c1.lis2ds12 \
    --sensor-samples ./samples/common/data/magic_wand/magic_wand.data \
    --trace-output trace.ctf \
    --timeout 10
```

This demo will for 10 seconds until a timeout is reached.
After this time, CTF traces returned over secondary UART will be stored in `trace.ctf`.

:::{note}
For trace collection on actual hardware, refer to [Trace collection](#trace-collection).
:::

The trace needs to be converted to the TEF format, so that it can be loaded in Zeppelin Trace Viewer.

For that purpose, run:

```bash
west zpl-prepare-trace ./trace.ctf --tvm-model-path samples/common/tvm/model/magic-wand-graph.json -o ./tef_tvm_profiler.json
```

The part `--tvm-model-path` is an input argument with the path to a TVM model graph, which is used to introduce additional model data to the TEF trace file metadata.

To get an overview of the traces, load the output `tef_tvm_profiler.json` file in [Zeppelin Trace Viewer](https://antmicro.github.io/zeppelin-trace-viewer).

## Customizing and using Zeppelin

Zeppelin can be enabled by y-selecting the `CONFIG_ZPL` symbol in the project configuration file.
To initialize Zeppelin in a runtime, use the `zpl_init()` function defined by the `zpl/lib.h` header.
You can enable various Zeppelin components by using Kconfig and runtime configuration, as described in following sections.

### Configuration

The library can be configured both during building and during a run on a device.
To find out how to configure the library and how to add new configurations, check {doc}`configuration`.

### Trace collection

To enable Zeppelin tracing support, the user should enable the symbol `CONFIG_ZPL_TRACE` in Kconfig.
You can then select one of the following formats:

* Plaintext format, by y-selecting `CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT`
* Common Trace Format (CTF), by y-selecting `CONFIG_ZPL_TRACE_FORMAT_CTF`

You can choose how the traces will be delivered to the host PC by selecting one of the available tracing backends:

* UART, by y-selecting `CONFIG_ZPL_TRACE_BACKEND_UART`
* USB, by y-selecting `CONFIG_ZPL_TRACE_BACKEND_USB`
* Debugger, by y-selecting `CONFIG_ZPL_TRACE_BACKEND_DEBUGGER`
* Renode's simulated trivial UART, by y-selecting `CONFIG_ZPL_TRACE_BACKEND_TRIVIAL_UART`

Depending on the tracing backend used, the following commands can be used for trace capture.

#### UART

* Config option - `CONFIG_ZPL_TRACE_BACKEND_UART`
* Command:
  ```bash
  west zpl-uart-capture [-h] serial_port serial_baudrate output_path

  Capture traces using UART. This command capures traces using the serial interface.

  positional arguments:
    serial_port      Seral port
    serial_baudrate  Seral baudrate
    output_path      Capture output path

  options:
    -h, --help       show this help message and exit
  ```

#### USB

* Config option - `CONFIG_ZPL_TRACE_BACKEND_USB`
* Command:
  ```bash
  west zpl-usb-capture [-h] [-t TIMEOUT] [-w] vendor_id product_id output_path

  Capture traces using USB. This command capures traces using USB.

  positional arguments:
    vendor_id             Vendor ID
    product_id            Product ID
    output_path           Capture output path

  options:
    -h, --help            show this help message and exit
    -t, --timeout TIMEOUT
                          Timeout of the USB capture in seconds
    -w, --wait-for-device
                          When this flag is set, the command will wait for the device to connect
  ```

#### Debugger

* Config option - `CONFIG_ZPL_TRACE_BACKEND_DEBUGGER`
* Command:
  ```bash
  west zpl-gdb-capture [-h] elf_path output_path

  Capture traces using GDB. This command captures traces using GDB from RAM using the `dump` command.

  positional arguments:
  elf_path     Zephyr ELF path
  output_path  Capture output path

  options:
  -h, --help   show this help message and exit
  ```

#### Trivial UART in Renode

On top of the above, Renode's simulated trivial UART can be used as well to collect traces in a simulation: `CONFIG_ZPL_TRACE_BACKEND_TRIVIAL_UART`.

### Adding named events to traces

Zeppelin provides methods for introducing custom named events to traces from the source code level.
To use named events, include the header `zpl/lib.h`, and use the function `sys_trace_named_event()` to generate named events.

### Memory profiler

To use Zeppelin memory profiler, y-select the `CONFIG_ZPL_MEMORY_PROFILING` in Kconfig.
No further actions are needed in the application code to generate memory profiling events in the generated trace.
Memory profiling along with memory events are described in {doc}`memory_profiling`.

### TLFM events

To use Zeppelin custom events with Tensorflow Lite Micro (TLFM), use the functions `zpl_emit_tflm_begin_event()` and `zpl_emit_tflm_end_event()`, provided by `zpl/tflm_events.h`.

## Testing Zeppelin

To run unit and integration tests, use the following commands:
```bash
west twister -v -p max78002evkit/max78002/m4 -p max32690fthr/max32690/m4 -p qemu_cortex_m3 -T samples -T tests
```
