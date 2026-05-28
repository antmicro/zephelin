# Introduction

Zephyr Profiling Library (ZPL), or Zephelin for short, is a library which enables capturing and reporting runtime performance metrics, for the profiling and detailed analysis of Zephyr applications, with a special focus on applications running AI/ML inference workloads.

This documentation describes the following aspects of Zephelin and the associated projects:

* {doc}`library` - provides general information on Zephelin repository, describes how to build, test and use the profiling middleware
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
* {doc}`development` - summarizes and links resources regarding development of Zephelin
* {doc}`benchmark_report` - provides details on the overhead introduced by the library based on different options
