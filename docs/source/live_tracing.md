# Real-time tracing

This chapter covers the usage of [Zephelin Trace Viewer](visual_interface) for live visualization of the traces being gathered during application execution.

:::{note}
Real-time visualization requires running a local Python server responsible for ingesting CTF traces, parsing them into TEF, and forwarding them to the visualizer.
:::

## Prerequisites

Before running the server, you need to install required backend dependencies and compile the frontend visualizer.

**1. Install server dependencies**

From the root of the project, run the following command:

```bash
pip install -r server/requirements.txt
```

**2. Build the Visualizer**

The server requires a compiled version of the [Zephelin Trace Viewer](visual_interface).
After cloning the repository, build the frontend by running:
```bash
yarn build
```

## Running the server

To start the Zephelin Server and host the visualizer, execute the `run_backend.py` script.

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
* `--frontend-directory` - Path to compiled frontend directory.
* `--build-dir` - Path to the traced application build directory.
* `--tflm-model-paths` - Paths to the TFLM models.
* `--tvm-model-paths` - Paths to the TVM models.
* `--tvm-model-metadata-paths` - Paths to the TVM model metadata files.
* `--tvm-model-op-remove-prefix` - Regex pattern used for removing TVM operator prefixes.
* `--tvm-model-op-remove-suffix` - Regex pattern used for removing TVM operator suffixes.
* `--verbosity` - Set the logging verbosity level (`DEBUG, INFO, WARNING, ERROR, CRITICAL`).

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


## Server API reference

The Zephelin real-time tracing server supports the following JSON-RPC requests sent as rpc_request WebSocket event:

{{endpoints}}
