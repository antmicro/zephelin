# Live tracing of events from the board

This chapter covers the usage of [Zephelin Trace Viewer](visual_interface) for live visualization of traces being gathered during application execution.

Real-time visualization requires running a local Python server responsible for ingesting CTF traces, parsing them into TEF, and forwarding them to the visualizer.

## Real-time tracing server structure

```{pipeline_manager} Live tracing diagram
:spec: ./zephelin-flow-spec.json
:graph: ./zephelin-flow-graph-live.json
:preview: true
```

Compared to diagram from {ref}`zephelin-trace-collection`, instead of saving and converting complete CTF traces to TEF format and uploading them to Zephelin Trace Viewer, we continuously deliver traces over TCP to a Zephelin's server, convert them chunk by chunk to TEF format and deliver to Zephelin Trace Viewer over Remote Procedure Calls (RPC).

The Zephelin's server consists of:

* [Trace Handler](https://github.com/antmicro/zephelin/blob/main/server/handlers/trace_handler.py) - configures Parser Proxy, `libbtrace` live plugin and RPC Dispatcher and controls delivery of traces and commands to the Zephelin Trace Viewer.
* [RPC Dispatcher](https://github.com/antmicro/zephelin/blob/main/server/rpc_dispatcher.py) - sends and receives messages from Zephelin Trace Viewer.
* [Stream Parser Proxy](https://github.com/antmicro/zephelin/blob/main/server/handlers/trace_handler.py) - collects data from `west zpl-<backend>-capture` over TCP and subdivides it to the commands' stream and traces.
  Traces are delivered to `libbtrace` live plugin.
* [`libbtrace` live plugin](https://github.com/antmicro/libbtrace/tree/main/src/plugins/ctf/live-src) - receives parts of CTF traces and converts them to parts of TEF messages that are later delivered to Trace Handler.

## Prerequisites

Before running the server, you need to install required backend dependencies and compile the frontend visualizer.

### Install server dependencies

Apart from installing Zephelin's dependencies (see {ref}`setting-up-workspace`), server dependencies need to be installed as well with the following command:

```bash
pip install -r server/requirements.txt
```

### Build the frontend for Trace Viewer

The server requires a compiled version of the [Zephelin Trace Viewer](visual_interface).
First, clone the repository:

```bash
git clone --recursive https://github.com/antmicro/zephelin-trace-viewer.git
```

After cloning the repository, install `corepack` and install necessary dependencies with:

```bash
cd zephelin-trace-viewer
corepack enable
yarn
```

In the end, build the backend with:

```bash
yarn build
cd ..
```

Built frontend will be available under `./zephelin-trace-viewer/dist` directory.

## Running the server

To start the Zephelin Server and host the visualizer, execute the `server/run_backend.py` script.

### Basic usage

To run the server with default settings and serve the frontend, point it to the `dist` directory with the compiled frontend:

```bash
python server/run_backend.py --frontend-directory <path_to_dist>
```

### Configuration Options

You can customize the server's networking interfaces, and specify trace parsing options that will be used in [CTF to TEF](ctf_to_tef) conversion.

* `--tcp-server-host` - Address of the Zephelin TCP socket for CTF trace ingestion (Default: `127.0.0.1`).
* `--tcp-server-port`- Port of the Zephelin TCP socket for CTF trace ingestion (Default: `5000`).
* `--backend-host` - Address where the backend API and visualizer are hosted (Default: `127.0.0.1`).
* `--backend-port` - Port where the backend API and visualizer are hosted (Default: `8000`).
* `--bt-port` - Port used by `libbtrace` live plugin to collect pure CTF traces (Default: `42674`).
* `--frontend-directory` - Path to compiled frontend directory.
* `--build-dir` - Path to the traced application build directory.
* `--tflm-model-paths` - Paths to the TFLM models.
* `--tvm-model-paths` - Paths to the TVM models.
* `--tvm-model-metadata-paths` - Paths to the TVM model metadata files.
* `--tvm-model-op-remove-prefix` - Regex pattern used for removing TVM operator prefixes.
* `--tvm-model-op-remove-suffix` - Regex pattern used for removing TVM operator suffixes.
* `--verbosity` - Set the logging verbosity level (`DEBUG, INFO, WARNING, ERROR, CRITICAL`).

### Additional configuration options for tests

There is a possibility to run the server in a mock mode, where TEF traces are delivered as inputs and sent to the website at specified speed:

* `--mock-trace-file` - Path to the TEF/JSON trace file to use for the mock.
* `--mock-playback-speed` - Playback speed multiplier for the mock.

## Providing traces to the server

Once the server is running, it listens for CTF traces on the TCP socket.
To route the traces read from one of the available backends (described in [Trace Collection](trace-collection) section), `--send-to-remote` argument can be provided with TCP socket address specified.

**Example**:

```bash
west zpl-uart-capture /dev/pts/12 115200 ./trace-hw.ctf --send-to-remote 127.0.0.1:5000
```

## Live-tracing controls

If the Visualizer is connected to the server, the live-tracing controls are available on the top-bar.

* `Start streaming` - enables continuous rendering of received traces.
* `Stop streaming` - disables continuous rendering.
* `Collect` - visualizes all the traces gathered so far.
* `Stop Tailing` - Stops the default behavior in which viewport follows live edge of visualized trace.
* `Resume Tailing` - Snaps the viewport back to the live edge.

:::{note}
Additionally, `Alt`+`R` performs a hard reset of the tracing session, which restarts the `libbtrace` instance parsing the trace.
It should only be used to recover from a `libbtrace` failure, as it drops the traces gathered so far.

Such failure can manifest itself as the Trace Viewer no longer receiving any new events, even though the capture command keeps streaming data to the server, with a `libbtrace` error traceback printed in the server log.
:::

## Sample collection of traces

Let's run an application running profiling for TensorFlow Lite Micro model.

First of, let's build a sample application running two TensorFlow Lite Micro models, with increased number of iterations:

```bash
west build -p -b max32690fthr/max32690/m4 samples/profiling/tflm_multi_model -- -DCONFIG_ZPL_TRACE_FORMAT_CTF=y -DCONFIG_TRACING_BUFFER_SIZE=10000 -DCONFIG_BOOT_BANNER=n -DCONFIG_PRINTK=n -DCONFIG_LOG=n -DCONFIG_ZPL_SAMPLE_TFLM_NUM_ITERS=200
```

After this, run server for live tracing, providing paths to models:

```bash
python server/run_backend.py --frontend-directory ./zephelin-trace-viewer/dist --tflm-model-paths ./samples/common/tflm/model/magic-wand.tflite ./samples/common/tflm/model/sine.tflite
```

In the end, run collection of traces from:

* Renode:
  ```bash
  python scripts/run_renode.py --trace-output test.ctf --send-to-remote 127.0.0.1:5000
  ```
* From actual hardware (after flash), e.g.:
  ```bash
  west zpl-uart-capture <path-to-uart> 115200 ./trace-hw.ctf --send-to-remote 127.0.0.1:5000
  ```

## Live tracing with instrumentation

Traces produced by the [instrumentation subsystem](instrumentation) can be visualized live as well, as long as they are delivered over the same channel as the regular Zephelin traces.
This is the case for the tracing subsystem backend (`CONFIG_INSTRUMENTATION_BACKEND_TRACING_CORE=y`), which packs instrumentation events into a separate CTF stream of the regular trace.
Thanks to this, no additional capture command is needed - a single `west zpl-<backend>-capture` with `--send-to-remote` feeds both streams to the server.

Let's use the {zpl_repo}`samples/profiling/tflm_instrumentation` sample, which runs a TFLM model with both Zephelin profilers and the instrumentation subsystem enabled.

First, build the sample with the instrumentation tracing backend configuration:

```bash
west build -p -b max32690fthr/max32690/m4 samples/profiling/tflm_instrumentation -- \
  -DEXTRA_CONF_FILE="zpl.conf;instrumentation_tracing.conf"
```

Then, start the server, pointing it to the model used by the sample and to the build directory:

```bash
python server/run_backend.py --frontend-directory ./zephelin-trace-viewer/dist \
  --tflm-model-paths ./samples/common/tflm/model/sine.tflite \
  --build-dir ./build
```

Next, run collection of traces from:

* Renode:
  ```bash
  python scripts/run_renode.py --send-to-remote 127.0.0.1:5000 --pause
  ```
* From actual hardware (after flash), e.g.:
  ```bash
  west zpl-uart-capture <path-to-uart> 115200 ./trace-hw.ctf --send-to-remote 127.0.0.1:5000
  ```

:::{note}
Starting simulation with `--pause` allows to postpone the execution of the sample until the frontend is set up and ready.
When using actual hardware, the server will only start processing traces after board reset.
:::

Once the simulation is connected to the backend, open the visualizer at configured address (default: `http://127.0.0.1:8000`), press `Start streaming` and unpause the simulation.

::::{only} html
The recording below shows the sample being visualized live.

:::{note}
The presented trace was gathered using Renode.
Running the sample on actual hardware may result in extended execution time due to instrumentation overhead.
:::

```{raw} html
<video controls playsinline preload="metadata" width="100%" style="max-width: 100%;">
  <source src="https://dl.antmicro.com/kenning/media/live_tracing_instrumentation.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>
```
::::

## Communication flow

Server implementation in `server/run_backend.py` consists of following access points:

* `<tcp_server_host>:<tcp_server_port>` - allows communication between `west` capture subcommands and the server.
* `<backend_host>:<backend_port>` - this hosts the website loaded from `--frontend-directory` directory and configures communication between website and server.
* `127.0.0.1:<bt_port>` - allows delivery of pure CTF events to the `libbtrace` live plugin (it is a one-way communication).

As in file-based Zephelin flow, the traces are first collected and sent by the board to the host using a selected backend (e.g. UART).
After this, `west zpl-<backend>-capture` command with `--send-to-remote` flag configured to e.g. `127.0.0.1:5000` will send CTF traces with additional data (such as `_zpl_ctf_start__` start tag) to a given address.

This address should match `--tcp-server-host` and `--tcp-server-port` settings in the `server/run_backend.py` script.
[`Stream Parser Proxy`](https://github.com/antmicro/zephelin/blob/main/server/handlers/trace_handler.py) will receive packets sent by the `west` subcommand and subdivide them into commands (such as restart the viewer based on start tag) that should be sent as RPC commands to the website, and pure CTF events.

Pure CTF events are sent to [`libbtrace` live plugin](https://github.com/antmicro/libbtrace/tree/main/src/plugins/ctf/live-src) over `--bt-port` port on loopback (e.g. `127.0.0.1:42674`), for fast conversion to TEF events in C++.
The plugin communicates with the `libbtrace` module running in the server, delivering `bt2` messages with parts of parsed TEF events - it is not socket-based communication.

:::{note}
It is possible to deliver pure CTF events directly to `libbtrace` live plugin by sending events directly to `--bt-port`, skipping the `Stream Parser Proxy`.
:::

Those `bt2` messages are delivered to the [`Trace Handler`](https://github.com/antmicro/zephelin/blob/main/server/handlers/trace_handler.py).
Trace Handler performs final adjustments of the TEF events and sends them to the website.

In the meantime, [`RPC Dispatcher`](https://github.com/antmicro/zephelin/blob/main/server/rpc_dispatcher.py) allows sending calls between server and website, and controls the state of the Zephelin Trace Viewer using procedures described in {ref}`server-api-reference`.

(server-api-reference)=
## Server API reference

The Zephelin real-time tracing server supports the following JSON-RPC requests sent as rpc_request WebSocket event:

{{endpoints}}
