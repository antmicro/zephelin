# Zephelin configuration

The library can be configured at build-time as well as at runtime.

## Configuring the library

To enable Zephelin's tracing support, enable the symbol `CONFIG_ZPL_TRACE` in Kconfig.

### Build-time configuration

The build-time configuration can only be selected during build-time.
The configuration can either be appended to the conf files:

```
CONFIG_ZPL_MEMORY_PROFILING=y
```

Or appended to the build command:

```bash
west build -b stm32f429i_disc1/stm32f429xx samples/trace/tflm_profiler -- -DCONFIG_ZPL_MEMORY_PROFILING=y
```

### Runtime configuration

A set of configuration flags defines runtime configuration.
Each flag denotes whether a corresponding configuration (e.g. memory profiling) is enabled or disabled.

By default, all flags are set.

#### Guards

In the code, there are two ways to use the runtime configuration as guards for the functionalities.

##### Wait-for function

The "wait-for" function stops the thread and waits for a signal.
Once the signal arrives, the thread is woken up and continues execution.
This is useful when the functionality which this configuration guards is in a separate thread.
This "wait-for" functionality can be called using the macro `ZPL_CONF_WAIT`.
Example:

```c
while (true) {
    ZPL_CONF_WAIT(memory_profiler);
    // ... Guarded code
}
```

:::{note}
The code is guarded only if the given configuration is defined with `threading` parameter set to `1`.
See [adding new configuration entry](#new-configuration-entry) for details.
:::

##### Is-enabled function

The "is-enabled" functionality doesn't stop the thread, and only checks if the configuration is turned on.
The function returns a boolean value, which can be checked in a standard "if", to create a guard for the functionality.
The "is-enabled" function can be called using the macro `ZPL_CHECK_IF_CONF`.
Example:

```c
if (ZPL_CONF_IS_ENABLED(memory_profiler)) {
    // ... Guarded code
}
```

(return-if-disabled)=
##### Return-if-disabled function

The "return-if-disabled" is a convenience macro using `ZPL_CONF_IS_ENABLED` to return if it evaluates to `false`.
The check-if function can be called using the macro `ZPL_CONF_RETURN_IF_DISABLED`.
Example:

```c
void zpl_profile_stack(const struct k_thread *thread, void *user_data) {
    ZPL_CONF_RETURN_IF_DISABLED(memory_profiler);
    // ... Guarded code
}
```

#### Interfaces

The runtime configuration supports the following interfaces:

* C API,
* UART shell commands,
* debug flags.

##### C API

To toggle configuration from the code, use the `ZPL_CONF_SET` macro, e.g.:

```c
#include <zpl/configuration.h>

int main(void) {
    ZPL_CONF_SET(inference, false);
    /* ... */
    ZPL_CONF_SET(inference, true);
    /* ... */
}
```

##### UART commands

UART commands runtime configuration can be enabled by selecting the Kconfig option `CONFIG_ZPL_RUNTIME_CONFIG_UART`.
This option enables runtime configuration via shell module with custom configuration commands.

To display the available configs type `help`:

```
uart:~$ help
Available commands:
  help
  inference
  memory
  memory_profiler
```

Each config can then be either enabled or disabled using the following syntax:

```
<command> enable
<command> disable
```

For example, this would be the memory profiler configuration:

```
memory_profiler enable
memory_profiler disable
```

##### Debug interface

You can use the debug configuration either directly from GDB, or using the west command `zpl-debug-config`.
To use it directly in GDB, make sure to load the ELF file with debug symbols.
Then set the desired config to `0` (disable) or `1` (enable):

```
set var debug_configs.<config> = <value>
```

For example, to enable the memory usage tracing, use the command:

```
set var debug_configs.memory_profiler = 1
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
west zpl-debug-config build/zephyr/zephyr.elf memory_profiler enable
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

## Profiling tiers

The library supports three distinct profiling tiers, each offering a different balance of performance impact and tracing detail:
* `ZPL_TRACE_MINIMAL_MODE` - this mode provides extremely lightweight profiling with minimal overhead.
  * It is designed for environments where performance is critical, and persistent trace data is not required.
  * When enabled, it activates basic inference profiling (`ZPL_INFERENCE_PROFILING`) and memory usage tracing (`ZPL_MEMORY_USAGE_TRACE`) to give a high-level view of system behavior without introducing measurable latency.

* `ZPL_TRACE_LAYER_PROFILING_MODE` - this mode enables layer-level timing.
  * It offers more granularity by tracking timing at individual model layers.

* `ZPL_TRACE_FULL_MODE` - this comprehensive profiling mode enables complete tracing.
  * This mode is suitable for in-depth debugging and performance analysis but incurs a higher runtime cost due to its extensive trace capture.
  * It includes all basic and layer-level profiling features, and additionally employs a wide array of kernel and runtime tracing subsystems, which include:
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

(adding-new-configurations)=
## Adding new configurations

Depending on the selected Zephelin integration, the source files in projects need to be adjusted, as described in the following subsections.

### Build-time configuration

The build-time configurations can be added to the {zpl_repo}`zpl/Kconfig` file.
The config should follow the Kconfig standard.
For example:

```
config ZPL_RUNTIME_CONFIG_UART
    bool "Runtime configuration via UART"
```

It can later be used to decide whether a corresponding functionality should be defined:

* in code, e.g. for function declarations:

```c
#ifdef CONFIG_ZPL_RUNTIME_CONFIG_UART
/* ... */
#endif
```

* in CMake, e.g. for including sources with function definitions:

```cmake
zephyr_library_sources_ifdef(CONFIG_ZPL_RUNTIME_CONFIG_UART configuration_uart.c)
```

### Runtime configuration

New runtime configurations can be defined in the configuration source files.

#### New configuration entry

To add a new configuration entry, add it to the list of existing ones in {zpl_repo}`include/zpl/configuration.h`, e.g.:

```C
#define CONFIGS(CONFIG)                                                           \
    /* ... */                                                                     \
    ZPL_IMPL_IF_ENABLED(CONFIG_ZPL_MEMORY_PROFILING,    CONFIG)                   \
        (memory_profiler, IS_ENABLED(CONFIG_ZPL_MEMORY_PROFILING_CONF_THREADING)) \
    /* ... */
```

where:

* `CONFIG` is the macro defining configuration functionality,
* `ZPL_IMPL_IF_ENABLED(CONFIG_ZPL_MEMORY_PROFILING,    CONFIG)` decides whether a provided `CONFIG` should be expanded,
* `(memory_profiler, IS_ENABLED(CONFIG_ZPL_MEMORY_PROFILING_CONF_THREADING))` defines `CONFIG` arguments:
    1. name of the configuration,
    2. threading flag indicating whether a given configuration should define
       mutexes, conditional variables, and thread-safe mechanisms.

This will automatically attach existing logic to a given configuration entry.

#### New configuration functionality

To extend the configuration capabilities, add new `CONFIGS` invocations or change the definition of an argument macro:

* adding declaration:

```c
// include/zpl/configuration.h

#define ZPL_CONF_WAIT_DECLARE(name)  /* ... */
#define ZPL_CONF_DECLARE(name, ...) \
    /* ... */                       \
    ZPL_CONF_WAIT_DECLARE(name)     \
    /* ... */
CONFIGS(ZPL_CONF_DECLARE)
```

* adding definition:

```c
// zpl/configuration.c

#define ZPL_CONF_WAIT_DEFINE(name)  /* ... */
#define ZPL_CONF_DEFINE(name, threading, ...) \
    /* ... */                                 \
    ZPL_CONF_WAIT_DEFINE(name, threading)     \
    /* ... */
CONFIGS(ZPL_CONF_DEFINE)

// or invoke `CONFIGS` separately, e.g. in zpl/configuration_uart.c

#define ZPL_CONF_SHELL_DEFINE(name, ...) /* ... */
CONFIGS(ZPL_CONF_SHELL_DEFINE)
```
