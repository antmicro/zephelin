# Introduction

## Documentation outline

This documentation describes the following aspects of Zephelin and the associated projects:

* {doc}`introduction` - provides general information on Zephelin, its use cases and capabilities
* {doc}`library` - describes how to build, test and use the profiling middleware
* {doc}`configuration` - describes build-time and runtime configuration of Zephelin library
* {doc}`memory_profiling` - describes memory profiling, along with memory events
* {doc}`code_scopes` - describes the use of tracing code scopes
* {doc}`debug_capture` - provides information on the debug interface for capturing traces
* {doc}`instrumentation` - shows how to use instrumentation subsystem with Zephelin
* {doc}`ctf_to_tef` - describes how traces are converted and processed
* {doc}`new_runtime` - depicts how to track a new runtime
* {doc}`visual_interface` - describes the tool for trace visualization and provides sample applications for various tracing features
* {doc}`live_tracing` - describes how to trace the execution in real-time
* {doc}`examples` - aggregates and describes various example applications present in the project
* {doc}`troubleshooting` - collects the most common problems with building, capturing and converting traces, along with their solutions
* {doc}`development` - summarizes and links resources regarding development of Zephelin
* {doc}`benchmark_report` - provides details on the overhead introduced by the library based on different options

## Zephelin

Zephyr Profiling Library (ZPL), or Zephelin for short, is a library which enables capturing and reporting runtime performance metrics, for the profiling and detailed analysis of Zephyr applications, with a special focus on applications running AI/ML inference workloads.

It collects traces from execution with either:

* **Tracing subsystem and predefined or user-provided events** - allowing to track functions, sections of code, loops, etc.
* **Instrumentation subsystem** - allowing to leverage the instrumentation feature of a compiler to automatically trace functions defined in the source, with a possibility to filter functions of interest

Zephelin is an [official external module for Zephyr RTOS](https://docs.zephyrproject.org/latest/develop/manifest/external/zephelin.html).

## Use cases for Zephelin

Zephelin can be used to analyze:

* Regular Zephyr applications
* Internals of the Zephyr RTOS with the help of the [instrumentation subsystem](instrumentation)
* AI models
* AI runtimes
* Multithreaded applications

(zephelin-trace-collection)=
## Zephelin trace collection

```{pipeline_manager}
:spec: ./zephelin-flow-spec.json
:graph: ./zephelin-flow-graph.json
:preview: true
```

Zephelin collects:

* Traces
* User-defined code scopes
* CPU load
* Memory usage (from runtime and RAM/ROM reports)
* Die temperature
* Model-related data:
    * Global - inference time
    * Per-layer:
        * Memory consumption
        * Total runtime of each layer, and of each layer type
        * Dimensions of tensors

The above data is later processed by `west zpl-<backend>-capture` commands (described in [Trace collection](#trace-collection)) and enhanced using `west zpl-prepare-trace` (described in [CTF and TEF trace processing](ctf_to_tef)).