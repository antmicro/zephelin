# Instrumentation

The [instrumentation subsystem](https://docs.zephyrproject.org/latest/samples/subsys/instrumentation/README.html) leverages the [GCC feature](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html) to insert custom code right before and after a function calls for profiling and tracing applications.

## Capturing trace

Currently, the instrumentation subsystem supports two tracing backends:

* UART
* Tracing subsystem

### UART

It can be enabled with `CONFIG_INSTRUMENTATION_BACKEND_UART=y`.

When using standalone UART backend, Zephelin provides the `west zpl-instrumentation-uart-capture` command to collect instrumentation traces:

```bash
west zpl-instrumentation-uart-capture [-h] \
     serial_port serial_baudrate output_path
```

It requests the trace by sending `dump_trace` message and waits for a response.
To make sure the received data is not contaminated by e.g. log messages, it is sent wrapped with `-*-#...-*-!`.
Base on that, the command finds the beginning and the end of message and saves trace in CTF format.

In case regular Zephelin traces are collected as well, it requires handling both channels of traces separately.

### Tracing subsystem

This backend can be enabled with `CONFIG_INSTRUMENTATION_BACKEND_TRACING_CORE=y`.

Instrumentation traces are packed together with regular traces in a separate CTF stream, allowing communication to be sent over single channel, either UART, USB or GDB.

When using tracing subsystem backend, instrumentation traces can be collected with the same `west` subcommand as regular traces, `zpl-uart-capture`:
```bash
  west zpl-uart-capture [-h] \
    serial_port serial_baudrate output_path
```

In order to visualize the trace with [Zephelin Trace Viewer](visual_interface), it has to be converted using `west zpl-prepare-trace -i {INSTRUMENTATION_CTF_TRACE} {CONVERTED_TRACE}`.
For more details, check out [CTF to TEF conversion](ctf_to_tef).

## Instrumentation with Zephelin's features

Instrumentation subsystem can also be used together with the rest of the Zephelin tracing systems.

The traces from the instrumentation subsystem are collected separately from the remaining tracing data.
The requirements for collecting all data are following:

* A different backend or connection type for instrumentation subsystem and the rest of traces - can be e.g. UART backend for instrumentation and RAM backend for other traces.
* A CTF format for the remaining traces (configurable with `CONFIG_ZPL_TRACE_FORMAT_CTF=y`)

With this, a following `west` subcommand can be used to capture both instrumentation and Zephelin traces at the same time:

```bash
west zpl-instrumentation-uart-gdb-capture [-h] \
     serial_port serial_baudrate instr_output_path output_path
```

The command uses UART to capture instrumentation trace (with the same logic as `zpl-instrumentation-uart-capture`) and GDB is used to extract remaining traces from RAM (as in `zpl-gdb-capture`).
The produced files have to be converted to TEF and combined into one trace with `west zpl-prepare-trace -i {INSTRUMENTATION_TRACE} {ZEPHELIN_TRACE} {TEF_TRACE}`.
The merging mechanism also ensures that traces do not collide and can be visualized.

:::{only} html and trace_viewer
Interactive version of instrumentation examples:
* [LiteRT runtime](_static/trace_viewer/index.html#profileURL=./tef_tflm_instrumentation.json){.external}
* [microTVM runtime](_static/trace_viewer/index.html#profileURL=./tef_tvm_instrumentation.json){.external}
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

Disabling instrumentation using the aforementioned options does not affect functions called from within excluded functions.
To disable instrumentation of functions called within excluded function, enable `CONFIG_INSTRUMENTATION_RECURSIVE_EXCLUDE` and list function names in `CONFIG_INSTRUMENTATION_RECURSIVE_EXCLUDE_LIST`.
Ensure that functions listed in `CONFIG_INSTRUMENTATION_RECURSIVE_EXCLUDE_LIST` are not excluded using the non-recursive methods (e.g. `__no_instrumentation__`), because this will prevent the recursive exclusion flags from being set.

Instrumentation subsystem provides a list of default excludes designed to prevent instrumentation of the instrumentation and tracing subsystems.
Before configuring custom excludes, consider appending them to the defaults.

### Dumping events when instrumentation buffer is full

Instead of disabling instrumentation subsystem when buffer is filled or overwriting the existing data, the subsystem can also dump all events to make space in the buffer.
This option can be enabled with `CONFIG_INSTRUMENTATION_MODE_CALLGRAPH_DUMP_ON_FULL=y`.

The `zpl-instrumentation-uart-capture` and `zpl-instrumentation-uart-gdb-capture` commands can automatically detect whether `DUMP_ON_FULL` was used and adjust capturing mechanism accordingly.
Similarly to Zephelin, instrumentation subsystem sends init tag at the start of the application.
It is detected by the `west` commands, to save traces into separate file, therefore it is advised to start `zpl-instrumentation-uart-capture` command before flashing or restarting the board.
Next, the commands wait for binary messages until user stops it or there is no new message received in specified timeout.
Also, to make sure all events are captured, after the timeout, the commands send `dump_trace` and gather remaining data from the buffer.

The example of this mechanism can be found in {zpl_repo}`samples/profiling/tflm_instrumentation`.

### Separating instrumentation traces from regular traces

To visually separate instrumentation traces from regular traces in [Zephelin Trace Viewer](visual_interface), the `--separate-instr-pid` option can be passed to `west zpl-prepare-trace`.
Instrumentation traces will be placed on a separate profile with its name matching the original thread name but with `(instrumentation)` suffix added.
Using this option avoids the need to tamper with event timestamps to align both types of traces.
