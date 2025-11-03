# Instrumentation

The [instrumentation subsystem](https://docs.zephyrproject.org/latest/samples/subsys/instrumentation/README.html) leverages the [GCC feature](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html) to insert custom code right before and after a function calls for profiling and tracing applications.

## Capturing trace

Currently instrumentation subsystem supports one tracing backend - UART.
Zephelin provides a `zpl-instrumentation-uart-capture` West subcommand to collect instrumentation traces:

```bash
west zpl-instrumentation-uart-capture [-h] \
     serial_port serial_baudrate output_path
```

It requests the trace by sending `dump_trace` message and waits for a response.
To make sure the received data is not contaminated by e.g. log messages, it is sent wrapped with `-*-#...-*-!`.
Base on that, the command finds the beginning and the end of message and saves trace in CTF format.

In order to visualize the trace with [Zephelin Trace Viewer](visual_interface), it has to be converted using `west zpl-prepare-trace -i {INSTRUMENTATION_CTF_TRACE} {CONVERTED_TRACE}`.
For more details, check out [CTF to TEF conversion](ctf_to_tef).

## Instrumentation with Zephelin's features

Instrumentation subsystem can also be used together with the rest of the Zephelin tracing systems.

The traces from the instrumentation subsystem are collected separately from the remaining tracing data.
The requirements for collecting all data are following:

* A different backend or connection type for instrumentation subsystem and the rest of traces - can be e.g. UART backend for instrumentation and RAM backend for other traces.
* A CTF format for the remaining traces (configurable with `CONFIG_ZPL_TRACE_FORMAT_CTF=y`)

With this, a following West subcommand can be used to capture both instrumentation and Zephelin traces at the same time:

```bash
west zpl-instrumentation-uart-gdb-capture [-h] \
     serial_port serial_baudrate instr_output_path output_path
```

The command uses UART to capture instrumentation trace (with the same logic as `zpl-instrumentation-uart-capture`) and GDB is used to extract remaining traces from RAM (as in `zpl-gdb-capture`).
The produced files have to be converted to TEF and combined into one trace with `west zpl-prepare-trace -i {INSTRUMENTATION_TRACE} {ZEPHELIN_TRACE} {TEF_TRACE}`.
The merging mechanism also ensures that traces do not collide and can be visualized.

:::{only} html and trace_viewer
Interactive version of instrumentation examples:
* <a href="_static/trace_viewer/index.html#profileURL=./tef_tflm_instrumentation.json">LiteRT runtime</a>
* <a href="_static/trace_viewer/index.html#profileURL=./tef_tvm_instrumentation.json">microTVM runtime</a>
:::

## Additional options

### Running without retained memory

By default, the instrumentation subsystem uses [retained memory](https://docs.zephyrproject.org/latest/hardware/peripherals/retained_mem.html) in order to configure trigger and stopper functions via UART, and persistently store them as long as the device is powered.

Instrumentation subsystem can also be run without retained memory by disabling `CONFIG_INSTRUMENTATION_DYNAMIC_TRIGGER`.
Then, trigger and stopper functions have to be selected with `CONFIG_INSTRUMENTATION_TRIGGER_FUNCTION` and `CONFIG_INSTRUMENTATION_STOPPER_FUNCTION` specifying mangled names of the functions.

### Enabling and disabling instrumentation for Zephelin internals

A function can be excluded from the instrumentation in a few ways:
* `__no_instrumentation__` attribute added to the function definition,
* function name (not mangled) added to the `CONFIG_INSTRUMENTATION_EXCLUDE_FUNCTION_LIST`,
* file path containing the function code added to the `CONFIG_INSTRUMENTATION_EXCLUDE_FILE_LIST`.

Zephelin disables instrumentation of its internal functions by default to not pollute traces with events unrelated to the profiled application.
It is achieved by adding source files to the exclude file list and using:
* `__no_zpl_instrumentation__` - extension of `__no_instrumentation__` attribute that can be disabled with a custom config,
* `ZPL_DISABLE_INSTRUMENTATION` - macro disabling instrumentation for a given code scope, it is not compatible with mechanisms jumping out of the given code scope.

In order to enable instrumentation for Zephelin's internal functions the `CONFIG_ZPL_INTERNALS_INSTRUMENTATION` can be used.
It prevents source file from being added in the exclude list and disables both `__no_zpl_instrumentation__` and `ZPL_DISABLE_INSTRUMENTATION`.
