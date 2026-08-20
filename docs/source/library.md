# Using and customizing Zephelin

(setting-up-workspace)=
## Initializing the workspace

First, make sure all dependencies required by [Zephyr RTOS](https://www.zephyrproject.org/) are installed - follow the [Getting started guide](https://docs.zephyrproject.org/latest/develop/getting_started/index.html).

Secondly, create a workspace and clone the Zephelin repository:

```bash
mkdir workspace && cd workspace
git clone --recursive git@github.com:antmicro/zephelin.git
cd zephelin
```

Then, install `west` and additional dependencies listed in the project's `requirements.txt` with `pip`:

```bash
pip install -r requirements.txt
```

Next, pick the Zephyr version to build against and initialize the workspace using West.
Pass the version to the script, or set `ZEPHYR_VERSION` to choose it (the supported values are the file names in `zephyr-versions/`).

```bash
source ./scripts/zephyr_version.sh v4.4.1
west init -l . --mf "$ZPL_WEST_MANIFEST"
```

Download, patch and prepare the project sources using the following commands:

```
west update
west patch -b "$ZPL_PATCH_BASE" -l "$ZPL_PATCH_YML" apply
west zephyr-export
west packages pip --install
```

For testing without hardware in the loop, download Renode portable and add the download path to the `PATH` environment variable:
The workspace records which version it was initialized for, so from then on `scripts/zephyr_version.sh` picks that version up on its own.
To move an existing workspace to another version, run:

```bash
./scripts/switch_zephyr_version.sh <version>
```

It removes the outgoing version's patches, repoints the manifest, updates the modules and applies the incoming version's patches, in that order.
:::{note}
Two versions may expect different Zephyr SDKs.
:::

For testing without hardware in the loop, download Renode portable and add the download path to the `PATH` environment variable:

```{Warning}
Make sure to use Renode version v1.16.0.4276 or newer.
```

(setup-renode)=
::::{tabs}

:::{group-tab} Linux
```bash
wget https://builds.renode.io/renode-latest.linux-portable-dotnet.tar.gz
mkdir renode-portable
tar --strip-components=1 -C ./renode-portable -xvf renode-latest.linux-portable-dotnet.tar.gz
export PATH=$(pwd)/renode-portable:$PATH
export PYRENODE_BIN="$PWD/renode-portable/renode"
export PYRENODE_RUNTIME=coreclr
```
:::

:::{group-tab} Mac OS
```bash
wget https://dot.net/v1/dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --version 8.0.410
export PATH="$HOME/.dotnet:$PATH"

git clone https://github.com/renode/renode.git
pushd renode
./build.sh --net -t -n --host-arch arm64
popd

export PATH="$(pwd)/renode:$PATH"
export PYRENODE_BUILD_DIR="$PWD/renode"
export PYRENODE_RUNTIME=coreclr
```
:::
::::

Finally, download Zephyr SDK:

```bash
west sdk install
```

(running-samples)=
## Running a sample project with Zephelin

To collect traces and visualize them using Zephelin Trace Viewer, you can run {zpl_repo}`a simple demo with gesture recognition <samples/demo>`, based on the data from an accelerometer.
The default {zpl_repo}`configuration <samples/demo/prj.conf>` in this demo collects traces along with all possible additional information, like memory usage, die temperature, inference statistics, and more.
One UART provides logs from the application, whereas the other UART returns CTF traces.

### Running the demo in a Renode simulation

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

This demo will run for 10 seconds, until a timeout is reached.
Afterwards, CTF traces returned over the secondary UART will be stored in `trace.ctf`.

:::{note}
For trace collection on actual hardware, refer to [Trace collection](#trace-collection).
:::

The trace needs to be converted to a TEF file to be loaded into Zephelin Trace Viewer.

To do that, run:

```bash
west zpl-prepare-trace ./trace.ctf --tvm-model-path samples/common/tvm/model/magic-wand-graph.json -o ./tef_tvm_profiler.json
```

The `--tvm-model-path` element is an input argument with the path to a TVM model graph, which is used to introduce additional model data to the TEF trace file metadata.

To get an overview of the traces, load the output `tef_tvm_profiler.json` file in [Zephelin Trace Viewer](https://antmicro.github.io/zephelin-trace-viewer).

### Running the demo on HW

This demo can be also run on a physical MAX32690 Evaluation Kit using the ADXL345 accelerometer.
The accelerometer can be connected to `i2c0` as follows:
* `VIN` -> any 3v3 pin
* `GND` -> any ground pin
* `SDA` -> pin 7 on port `JH4`
* `SCL` -> pin 8 on port `JH4`

It is also required to connect the following jumpers to enable `i2c0`:
* `JP2`
* `JP3`
* `JP4`

To program the board, connect the MAX32625PICO using a USB cable to the PC, and via the `SWD` header to the board.
Then, connect another USB cable to `CN2` - this will be used to collect data via UART (`uart2`).
Finally, to collect the traces, connect USB-UART converter to `uart0` using following pins:
* `RX` - pin 11 on port `JH4`
* `TX` - pin 12 on port `JH4`

Alternatively, when the USB-UART converter is not available, it is possible to switch UARTs in the board overlay and collect traces the same way as logs - using `uart2`.

To build the demo, run:
```bash
west build -p -b max32690evkit/max32690/m4 samples/demo
```

And then, to flash the board, run:
```bash
west flash --openocd=${MSDK_OPENOCD}
```
using `openocd` from [Analog Devices MSDK](https://github.com/analogdevicesinc/msdk).

After flashing, there should be logged readings from the sensor to the UART.
```
*** Booting Zephyr OS build v4.2.0-rc2-49-g732a3a5c6655 ***
adxl345@53: x=+0.312 y=+0.906 z=+0.046
adxl345@53: x=+0.296 y=+0.906 z=+0.031
adxl345@53: x=+0.312 y=+0.890 z=+0.015
adxl345@53: x=+0.312 y=+0.890 z=+0.015
adxl345@53: x=+0.312 y=+0.890 z=+0.031
...
```

To trigger gesture recognition, move the sensor.
```
...
adxl345@53: x=-0.015 y=+0.374 z=+0.078
model output: wing=1.000 ring=0.000 slope=0.000 negative=0.000
```

Then, the traces collected via UART can be analyzed the same way as in [Running the demo in a Renode simulation](#running-the-demo-in-renode-simulation).

## Customizing and using Zephelin

Zephelin can be enabled by y-selecting the `CONFIG_ZPL` symbol in the project configuration file.
By default, Zephelin is automatically initialized during Zephyr initialization, but it can also be initialized in a runtime by setting the Kconfig symbol `CONFIG_ZPL_AUTORUN_INIT` to `n` and using the `zpl_init()` function defined by the `zpl/lib.h` header.
You can enable various Zephelin components by using Kconfig and runtime configuration, as described in the following sections.

:::{warning}
Manual and automatic initializations are mutually exclusive. Enabling `CONFIG_ZPL_AUTORUN_INIT` makes `zpl_init` local as a protection
against using both methods at the same time. Improper use will result in a compile-time error.
:::

### Configuration

The library can be configured both during building and while running on a device.
To find out how to configure the library and how to add new configurations, check {doc}`configuration`.

(trace-collection)=
### Trace collection

To enable Zephelin tracing support, the user should enable the symbol `CONFIG_ZPL_TRACE` in Kconfig.
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
  ```
  usage: west zpl-uart-capture [-h] [--send-enable] serial_port serial_baudrate output_path

  Capture traces using UART. This command captures traces using the serial interface.

  positional arguments:
    serial_port      Seral port
    serial_baudrate  Seral baudrate
    output_path      Capture output path

  options:
    -h, --help       show this help message and exit
    --send-enable    Send 'enable' to device before collecting data to enable tracing, requires
                     CONFIG_TRACING_HANDLE_HOST_CMD to be enabled in the app
    --send-to-remote
                     Forward collected data to specified address
  ```

#### USB

* Config option - `CONFIG_ZPL_TRACE_BACKEND_USB`
* Command:
  ```
  usage: west zpl-usb-capture [-h] [-t TIMEOUT] [-w] vendor_id product_id output_path

  Capture traces using USB. This command captures traces using USB.

  positional arguments:
    vendor_id             Vendor ID
    product_id            Product ID
    output_path           Capture output path

  options:
    -h, --help            show this help message and exit
    -t TIMEOUT, --timeout TIMEOUT
                          Timeout of the USB capture in seconds
    -w, --wait-for-device
                          When this flag is set, the command will wait for the device to connect
    --send-to-remote      Forward collected data to specified address
  ```

#### Debugger

* Config option - `CONFIG_ZPL_TRACE_BACKEND_DEBUGGER`
* Command:
  ```
  usage: west zpl-gdb-capture [-h] [--elf-path ELF_PATH] [--gdb-port GDB_PORT] [--gdb GDB]
                            [--no-debug-server] [--openocd OPENOCD]
                            [--buffer-full | --n-bytes N_BYTES]
                            output_path

  Capture traces using GDB. This command captures traces using GDB from RAM using the `dump` command.

  positional arguments:
    output_path          Capture output path

  options:
    -h, --help           show this help message and exit
    --elf-path ELF_PATH  Zephyr ELF path, by default deduced from Zephyr build dir
    --gdb-port GDB_PORT  GDB server port
    --gdb GDB            Path to GDB
    --no-debug-server    Don't set up the debug server
    --openocd OPENOCD    Path to custom OpenOCD
    --buffer-full        Run application until trace buffer is full
    --n-bytes N_BYTES    Run application until there is at least n in trace buffer
    --send-to-remote     Forward collected data to specified address
  ```

#### Trivial UART in Renode

On top of the above, Renode's simulated trivial UART can be used as well to collect traces in a simulation: `CONFIG_ZPL_TRACE_BACKEND_TRIVIAL_UART`.

### Adding named events to traces

Zephelin provides methods for introducing custom named events to traces from the source code level.
To use named events, include the header `zpl/lib.h`, and use the function `sys_trace_named_event()` to generate named events.

### Changing timestamp clock

By default, Zephelin uses kernel cycles for event timestamps. This can be overridden by y-selecting `CONFIG_ZPL_CONFIGURABLE_TIMESTAMP_CLOCK` and passing a structure to `zpl_clock_set`, which has the following definition:

```C
// zpl/time.h

typedef struct {
    uint64_t (*cycles_get)(void);
    uint64_t (*timestamp_get)(uint64_t cycles);
} zpl_clock_t;
```

This might be useful when the system clock is not synchronized between different Zephelin instances running at the same time.

An example can be found in {zpl_repo}`samples/basic/custom_clock/src/main.c`.

### Memory profiler

To use Zephelin's memory profiler, y-select the `CONFIG_ZPL_MEMORY_PROFILING` in Kconfig.
No further actions are needed in the application code to generate memory profiling events in the generated trace.
Memory profiling, along with memory events, are described in {doc}`memory_profiling`.

### TLFM events

To use Zephelin's custom events with Tensorflow Lite Micro (TLFM), use the functions `zpl_emit_tflm_begin_event()` and `zpl_emit_tflm_end_event()`, provided by `zpl/tflm_events.h`.

### Delayed emission of layer profiling events

By default, the TFLM and microTVM profilers emit a trace event on every operator boundary right when that boundary is reached.
Formatting and pushing an event into the tracing buffer takes time, and since it happens between the operators, that time is included in the inference being measured.

The delayed emission mechanism removes this overhead from the measurement.
When it is enabled, the profiler only reads the cycle counter at each operator boundary and stores the timestamps in memory.
All the events are formatted and emitted at once when the inference finishes.

The mechanism is disabled by default and can be enabled per runtime:

* `CONFIG_ZPL_TFLM_PROFILER_DELAYED_EMISSION` for TFLM,
* `CONFIG_ZPL_TVM_PROFILER_DELAYED_EMISSION` for microTVM.

The number of operator events buffered during a single inference is limited by `CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS` / `CONFIG_ZPL_TVM_PROFILER_MAX_EVENTS` (32 by default).
Operators beyond that limit are not traced, and a warning is logged.

:::{warning}
Delayed emission makes the trace stream non-chronological - the buffered operator events reach the host after events that were emitted while the inference was running (for example code scopes marked from an interrupt), but they carry earlier timestamps.

Offline processing with {doc}`ctf_to_tef` handles this, because the whole trace is sorted before conversion.
{doc}`live_tracing` does not - it converts and renders the events as they arrive, and the trace viewer drops events whose timestamp is older than the newest one already displayed for a given thread.
With delayed emission enabled, the layer profiling events are therefore likely to be lost in live tracing.
:::

## Testing Zephelin

To run unit and integration tests, use the following commands:
```bash
west twister -v -p max78002evkit/max78002/m4 -p max32690fthr/max32690/m4 -p qemu_cortex_m3 -T samples -T tests
```
