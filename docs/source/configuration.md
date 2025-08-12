# Zeppelin configuration

The library can be configured at build-time as well as at runtime.

## Configuring the library

### Build-time configuration

The buid-time configuration can only be selected during build-time.
The configuration can either be appended to the conf files:

```
CONFIG_ZPL_MEMORY_USAGE_TRACE=y
```

Or to the build command:

```
west build -b stm32f429i_disc1/stm32f429xx samples/trace/memory_profiling -- -DCONFIG_ZPL_MEMORY_USAGE_TRACE=y
```

### Runtime configuration

By default the runtime configuration is turned off with a Kconfig option `CONFIG_ZPL_RUNTIME_CONFIG_NONE`.
To turn it on, select one of the following runtime configuration types:

* `CONFIG_ZPL_RUNTIME_CONFIG_UART` - UART shell commands
* `CONFIG_ZPL_RUNTIME_CONFIG_DEBUG` - In-memory debug configuration

#### UART commands

UART commands runtime configuration can be enabled by selecting `CONFIG_ZPL_RUNTIME_CONFIG_UART` Kconfig option.
This option enables runtime configuration via shell module with custom configuration commands.

To display available configs type `help`:

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

For example the memory usage configuration:

```
mem_usage_trace enable
mem_usage_trace disable
```

#### Debug interface

Debug runtime configuration can be enabled by selecting `CONFIG_ZPL_RUNTIME_CONFIG_DEBUG` Kconfig option.
You can use the debug configuration either directly from GDB, or using the `zpl-debug-config` west command.
To use it directly in GDB, make sure to load the ELF file with debug symbols.
Then set the desired config to 0 (disable) or 1 (enable):

```
set var debug_configs.<config> = <value>
```

For example, to enable the memory usage tracing:

```
set var debug_configs.mem_usage_trace = 1
```

You can also use the `zpl-debug-config` west command:

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

For example, to enable the memory usage tracing:

```
west zpl-debug-config build/zephyr/zephyr.elf mem_usage_trace enable
```

## Adding new configurations

Adding new configurations requires a change in the sources files.

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

Then in each configuration type source file, define those functions, using the same name, and its corresponding Kconfig option.
For example in the `configuration_uart.c` file:

```c
ZPL_CONF_UART_DEF(config_name, kconfig_option)
```

In the code, there are two ways to use the runtime configuration as guards for the functionalities.

#### Wait-for function

The wait-for function stops the thread, and waits for a signal.
Once the signal comes, the thread is woken up and continues execution.
This is useful when the functionality we want the configuration to guard is in a separate thread.
This wait-for functionality can be called using a `ZPL_WAIT_FOR_CONF` macro.
Example:

```c
while (true) {
    ZPL_WAIT_FOR_CONF(mem_usage_trace);
    // ... Guarded code
}
```

#### Check-if function

The check-if functionality doesn't stop the thread, it only checks if the configuration is turned on.
The function returns a boolean value, which can be checked in a standard if, to create a guard for the functionality.
The check-if function can be called using a `ZPL_CHECK_IF_CONF` macro.
Example:

```c
if (ZPL_CHECK_IF_CONF(mem_usage_trace)) {
    // ... Guarded code
}
```

To use the runtime configuration functions in code
