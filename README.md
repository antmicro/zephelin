# Zeppelin - Zephyr AI Profiling Library

Copyright (c) 2025 [Analog Devices, Inc.](https://www.analog.com/en/index.html)

Copyright (c) 2025 [Antmicro](https://www.antmicro.com)

Zephyr Profiling Library (ZPL), or Zeppelin for short, is a library which enables capturing and reporting runtime performance metrics, for the profiling and detailed analysis of Zephyr applications, with a special focus on applications running AI/ML inference workloads.

[Zeppelin documentation](https://antmicro.github.io/zeppelin) | [Trace Viewer](https://antmicro.github.io/zeppelin-trace-viewer)

## Introduction

Zeppelin enables collecting detailed information on the execution process of your Zephyr applications.
It elevates various Zephyr RTOS subsystems to collect traces for the application, resource usage (CPU Load, usage of memory), or data from on-board sensors to track changes of temperature, and more.

In addition to the above, Zeppelin also simplifies the analysis of AI runtimes, such as LiteRT and microTVM, allowing you to gain a better understanding of the underlying bottlenecks or potential opportunities for optimization.

Zeppelin features:

* Tracing execution of Zephyr applications on hardware
* Obtaining traces using such backends as UART, USB or debug adapter
* Delivering traces in CTF and TEF formats
* Scripts for capturing traces from device
* Collecting readings from:
    * Memory - stack, heaps, kernel hepas and memory slabs
    * Sensors - e.g. die temperature sensors
    * Thread analysis - CPU usage
    * AI runtimes - e.g. tensor arena usage in LiteRT
* Displaying details on executed neural network layers in LiteRT or microTVM runtimes:
    * Dimensions of inputs, outputs and weights
    * Parameters of layers
    * Time and resources spent on executing specific layers
* Compilation-level and runtime-level configuration of the library
    * Ability to configure a profiling tier, controlling the subsystems and the amount of data collected

All of the above can be analyzed with [Zeppelin Trace Viewer](https://antmicro.github.io/zeppelin-trace-viewer).

## Installing project's requirements

Install `west` with `pip`:

<!-- name="pip-init" -->
```shell
pip install -r requirements.txt
```

Then, initialize the workspace using `west`:

<!-- name="west-init" -->
```shell
west init -l .
west update
west patch apply
west zephyr-export
west packages pip --install
west sdk install
source zpl_env.sh
```

In the end, download [Renode](https://renode.io) and configure environment variables for [pyrenode3](https://github.com/antmicro/pyrenode3) package:

```bash
wget https://builds.renode.io/renode-latest.pkg.tar.xz
export PYRENODE_PKG=$(pwd)/renode-latest.pkg.tar.xz
```

## Building samples

Run the following command:
<!-- name="build-samples" -->
```shell
west build -p -b max78002evkit/max78002/m4 samples/events/named_event
```

## Running example demo

To collect traces and visualize them using Zeppelin Trace Viewer, you can run [a simple demo with gesture recognition](./samples/demo), based on the data from an accelerometer in a Renode simulation.

The default [configuration](./samples/demo/prj.conf) in this demo collects traces along with all possibile additional information, like memory usage, die temperature, inference statistics, and more.

One UART provides logs from the application, whereas the other UART returns CTF traces.

To build the sample, run:

<!-- name="build-demo" -->
```shell
west build -p -b stm32f746g_disco/stm32f746xx samples/demo
```

To run it in a Renode simulation, run:

<!-- name="run-demo" -->
```shell
python ./scripts/run_renode.py \
    --repl ./samples/demo/boards/stm32f746g_disco_lis2ds12.repl \
    --sensor i2c1.lis2ds12 \
    --sensor-samples ./samples/common/data/magic_wand/magic_wand.data \
    --trace-output trace.ctf \
    --timeout 10
```

To load the traces, gathered in the file `trace.ctf`, into Zeppelin Trace Viewer, convert this file to the TEF format with:

<!-- name="convert-to-tef" -->
```bash
west zpl-prepare-trace ./trace.ctf --tvm-model-path samples/common/tvm/model/magic-wand-graph.json -o ./tef_tvm_profiler.json
```

In the end, load the file `./tef_tvm_profiler.json` [in the viewer](https://antmicro.github.io/zeppelin-trace-viewer).

## Convert the trace

The library produces traces in CTF (Common Trace Format), which, in order to be visualized, have to be converted to TEF (Trace Event Format).

This can be achieved with `west zpl-prepare-trace` command, which:
1. automatically prepares an environment (with combined metadata from Zephyr and Zeppelin, defining available events),
2. converts the trace, and
3. processes custom event:

```bash
west zpl-prepare-trace [-h] -o OUTPUT [--zephyr-base ZEPHYR_BASE]
                       [--tflm-model-path TFLM_MODEL_PATH]
                       [--tvm-model-path TVM_MODEL_PATH]
                       [--build-dir BUILD_DIR]
                       [--zephyr-elf-path ZEPHYR_ELF_PATH]
                       ctf_trace
```

## Setting up USB device permissions for Zeppelin

To use the USB backend and its associated `west zpl-usb-capture` command seamlessly,
use the following udev rule (example):
`/etc/udev/rules.d/99-zpl-usb-access.rules`:

```
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0456", ATTRS{idProduct}=="aa55", MODE="0666"
```

You might need to reload udev rules and trigger them manually, like so:
```bash
udevadm control --reload-rules
udevadm trigger
```
