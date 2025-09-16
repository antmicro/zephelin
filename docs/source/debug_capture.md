# Trace capture debug interface

Zephelin's debug interface enables for traces gathering via a GDB link.
The traces are stored in memory and can be extracted using a `zpl-gdb-capture` west command.

Examples on how to capture traces, both on physical hardware and in Renode, are described below.

## Physical hardware

Before capturing traces from a board, first make sure it's flashed with the firmware with `CONFIG_ZPL_TRACE_BACKEND_DEBUGGER` Kconfig option enabled.

1. Connect the board via the debug interface to your host
2. Run the `zpl-gdb-capture` command and wait for the capture to finish

```
west zpl-gdb-capture <elf_file> <output_trace>
```

:::{note}
The `zpl-gdb-capture` command runs the `west debugserver` command, so setting up the gdb server is not necessary.
:::

## Renode

Before capturing traces in Renode, first make sure firmware has been built with `CONFIG_ZPL_TRACE_BACKEND_DEBUGGER` Kconfig option enabled.

1. Run Renode using `west simulate`
2. Enable GDB server in Renode's monitor: `machine StartGdbServer 3333`
3. Run the `zpl-gdb-capture` command and wait for the capture to finish

```
west zpl-gdb-capture --no-debug-server <elf_file> <output_trace>
```
