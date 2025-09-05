# Zephelin configuration

The library can be configured at build-time as well as at runtime.

## Configuring the library

To enable Zephelin tracing support, enable the symbol `CONFIG_ZPL_TRACE` in Kconfig.

### Build-time configuration

The build-time configuration can only be selected during build-time.
The configuration can either be appended to the conf files:

```
CONFIG_ZPL_MEMORY_USAGE_TRACE=y
```

Or appended to the build command:

```
west build -b stm32f429i_disc1/stm32f429xx samples/trace/memory_profiling -- -DCONFIG_ZPL_MEMORY_USAGE_TRACE=y
```

### Runtime configuration

By default, the runtime configuration is turned off with a Kconfig option `CONFIG_ZPL_RUNTIME_CONFIG_NONE`.
To turn it on, select one of the following runtime configuration types:

* `CONFIG_ZPL_RUNTIME_CONFIG_UART` - UART shell commands
* `CONFIG_ZPL_RUNTIME_CONFIG_DEBUG` - In-memory debug configuration

#### UART commands

UART commands runtime configuration can be enabled by selecting the Kconfig option `CONFIG_ZPL_RUNTIME_CONFIG_UART`.
This option enables runtime configuration via shell module with custom configuration commands.

To display the available configs type `help`:

```
uart:~$ help
Available commands:
  help
  mem_usage_trace
```

Each config can then be either enabled or disabled using the following syntax:

```
<command> enable
<command> disable
```

For example, the memory usage configuration:

```
mem_usage_trace enable
mem_usage_trace disable
```

#### Debug interface

Debug runtime configuration can be enabled by selecting the Kconfig option `CONFIG_ZPL_RUNTIME_CONFIG_DEBUG`.
You can use the debug configuration either directly from GDB, or using the west command `zpl-debug-config`.
To use it directly in GDB, make sure to load the ELF file with debug symbols.
Then set the desired config to `0` (disable) or `1` (enable):

```
set var debug_configs.<config> = <value>
```

For example, to enable the memory usage tracing, use the command:

```
set var debug_configs.mem_usage_trace = 1
```

You can also use the west command `zpl-debug-config`:

```
usage: west zpl-debug-config [-h] elf_path config value

Enable/Disable configs in runtime using debug interface. This command can list available configs and enable/disable them.

positional arguments:
  elf_path    Zephyr ELF path
  config      Config to set
  value       Value of the config (enable/disable)

options:
  -h, --help  show this help message and exit
```

For example, to enable the memory usage tracing, use the command:

```
west zpl-debug-config build/zephyr/zephyr.elf mem_usage_trace enable
```

## Trace formats

The user can then select the following formats:

* Plaintext format, by y-selecting `CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT`
* Common Trace Format (CTF), by y-selecting `CONFIG_ZPL_TRACE_FORMAT_CTF`

## Trace backends

You can choose how the traces will be delivered to the host PC by selecting one of the available tracing backends:

* UART, by y-selecting `CONFIG_ZPL_TRACE_BACKEND_UART`
* USB, by y-selecting `CONFIG_ZPL_TRACE_BACKEND_USB`
* Debugger, by y-selecting `CONFIG_ZPL_TRACE_BACKEND_DEBUGGER`
* Renode's simulated trivial UART, by y-selecting `CONFIG_ZPL_TRACE_BACKEND_TRIVIAL_UART`

Depending on the tracing backend used, the following commands can be used for trace capture.

## Profiling tiers

The library supports three distinct profiling tiers, each offering a different balance of performance impact and tracing detail:
* `ZPL_TRACE_MINIMAL_MODE` - This mode provides extremely lightweight profiling with minimal overhead.
  * It is designed for environments where performance is critical, and persistent trace data is not required.
  * When enabled, it activates basic inference profiling (`ZPL_INFERENCE_PROFILING`) and memory usage tracing (`ZPL_MEMORY_USAGE_TRACE`) to give a high-level view of system behavior without introducing measurable latency.

* `ZPL_TRACE_LAYER_PROFILING_MODE` - This mode enables layer-level timing.
  * It offers more granularity by tracking timing at individual model layers.

* `ZPL_TRACE_FULL_MODE` - This comprehensive profiling mode enables complete tracing.
  * This mode is suitable for in-depth debugging and performance analysis but incurs a higher runtime cost due to its extensive trace capture.
  * It includes all basic and layer-level profiling features, and additionally implies a wide array of kernel and runtime tracing subsystems, which include:
    * syscall tracing,
    * thread scheduling,
    * interrupt service routines (ISRs),
    * synchronization primitives (semaphores, mutexes, condition variables),
    * IPC mechanisms (queues, FIFOs, LIFOs, stacks, message queues, mailboxes, pipes),
    * memory allocators (heap, memory slabs),
    * timers,
    * event handling,
    * polling,
    * power management,
    * networking (core, sockets),
    * various hardware interfaces (GPIO, idle state tracking).

## Adding new configurations

Depending on the selected Zephelin integration, the source files in projects need to be adjusted, as described in the following subsections.

### Build-time configuration

The build-time configurations can be added to the `zpl/Kconfig` file.
The config should follow the Kconfig standard.
For example:

```
config ZPL_RUNTIME_CONFIG_NONE
	bool "No runtime configuration"
```

### Runtime configuration

New runtime configurations can be defined in the configuration source files.
To add a new config, first, using macros, declare two functions in `include/zpl/configuration.h`:

```c
ZPL_WAIT_FOR_CONF_DEC(config_name)
ZPL_CHECK_IF_CONF_DEC(config_name)
```

Then, in each configuration type's source file, define those functions, using the same name, and its corresponding Kconfig option.
For example in the `configuration_uart.c` file:

```c
ZPL_CONF_UART_DEF(config_name, kconfig_option)
```

In the code, there are two ways to use the runtime configuration as guards for the functionalities.

#### Wait-for function

The "wait-for" function stops the thread, and waits for a signal.
Once the signal arrives, the thread is woken up, and continues execution.
This is useful when the functionality which this configuration guards is in a separate thread.
This wait-for functionality can be called using the macro `ZPL_WAIT_FOR_CONF`.
Example:

```c
while (true) {
    ZPL_WAIT_FOR_CONF(mem_usage_trace);
    // ... Guarded code
}
```

#### Check-if function

The "check-if" functionality doesn't stop the thread, and only checks if the configuration is turned on.
The function returns a boolean value, which can be checked in a standard "if", to create a guard for the functionality.
The check-if function can be called using the macro `ZPL_CHECK_IF_CONF`.
Example:

```c
if (ZPL_CHECK_IF_CONF(mem_usage_trace)) {
    // ... Guarded code
}
```
