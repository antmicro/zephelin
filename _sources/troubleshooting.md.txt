# Troubleshooting

This chapter collects the most common problems encountered when building applications with Zephelin, capturing traces and converting them for Zephelin Trace Viewer, together with their causes and solutions.

## Trace capture

### The capture command produces an empty or truncated file

Check the following, in order:

* `CONFIG_ZPL_TRACE` is enabled and one of the trace formats (`CONFIG_ZPL_TRACE_FORMAT_CTF` or `CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT`) is selected.
* The backend enabled in Kconfig matches the `west zpl-*-capture` command used - firmware built with `CONFIG_ZPL_TRACE_BACKEND_DEBUGGER` will not produce traces on UART.
* The capture is running while the traced code executes.

### The captured data is incomprehensive

* Verify you are reading the trace UART, not the console UART.
  The samples select the trace UART with the `zephyr,tracing-uart` chosen property in a board overlay (see {zpl_repo}`samples/common/boards`).
  If application logs are interleaved with the CTF stream, the trace is unparsable.
* With `CONFIG_ZPL_TRACE_FORMAT_CTF`, the file is binary by design - convert it with `west zpl-prepare-trace` into a `.tef` file and load it into Trace Viewer for inspection.
Traces generated with `CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT` cannot be converted.

### Events are missing or seem to never end

Events are staged in the Zephyr tracing buffer sized with `CONFIG_TRACING_BUFFER_SIZE` before the backend sends them out.
How an overflow manifests depends on the tracing mode:

* With `CONFIG_TRACING_ASYNC` (the Zephyr default), the buffer is a ring buffer and the packets that do not fit are dropped, which shows up as missing or unending events rather than as an error.
  Increase `CONFIG_TRACING_BUFFER_SIZE` - most samples use `4096`, and {zpl_repo}`samples/profiling/smp_tvm` needs `10240` - and, with the UART backend, use the highest baud rate supported by the board.
* With `CONFIG_TRACING_SYNC`, which most Zephelin samples enable, the buffer only holds a single formatted packet, so it has to be at least `CONFIG_TRACING_PACKET_MAX_SIZE` bytes.
  Nothing is dropped in this mode, but every event blocks the emitting thread until the backend accepts it.

### USB capture does not find the device

`west zpl-usb-capture` fails with `Couldn't open USB device with vid=... pid=...` when the device is not enumerated yet or the identifiers do not match.

* Use `-w`/`--wait-for-device` to wait for the board instead of failing immediately, which is useful when the board is reset after the command starts.
* Make sure the USB requirements described in {doc}`usb_requirements` are met.

## Converting traces

### `Zephyr CTF metadata (...) does not exist`

The conversion merges the Zephyr and Zephelin CTF metadata, and the Zephyr part is looked up relative to the Zephyr repository.
By default, the path is deduced from the script location inside the workspace, which fails when Zephelin is used outside of it.

Pass `--zephyr-base` to `west zpl-prepare-trace` or export `ZEPHYR_BASE`.

### Function names in the trace are mangled

C++ symbols are demangled with `c++filt` taken from the Zephyr SDK.
If the conversion prints `c++filt is missing`, point Zephelin at a working binary with the `ZPL_DEMANGLE_CMD` environment variable.

### Instrumentation events show raw addresses instead of function names

`No symbols found - using callee address ...` means the symbols could not be resolved from the ELF file.
The instrumentation trace has to be converted against the very same binary that was flashed on the device, so pass the matching `--build-dir` or `--zephyr-elf-path` and re-flash the board if the build directory has been rebuilt in the meantime.

## Live tracing

Live tracing is driven by the Zephelin server, which can be started either with `python server/run_backend.py` or with the `west zpl-live-server` command.
Both accept the same arguments and can be used interchangeably, so the options mentioned below apply to either of them.

### The viewer stays empty although the capture command reports incoming bytes

The server discards all incoming data until it finds the `_zpl_ctf_start__` synchronization tag, which is emitted by the device on startup.
If the capture is started while the application is already running, the tag never arrives.

Reset the board after connecting the capture, or start the Renode simulation with `--pause` and unpause it once the frontend is connected, as described in {doc}`live_tracing`.

### CPU load, memory or die temperature samples only appear at the end of the trace

The periodic profilers run in their own threads, with a default priority of 5.
An application that runs inferences back-to-back in a higher-priority thread without yielding starves them, so their events are only emitted once the busy loop ends, even though the trace pipeline works correctly.

Either add sleeps to the application loop, or raise the priority of the profiling threads, for example:

```
CONFIG_ZPL_CPU_LOAD_PROFILING_THREAD_PRIORITY=-1
CONFIG_ZPL_MEMORY_PROFILING_THREAD_PRIORITY=-1
```

The profiling threads sleep between the samples, so making them cooperative does not block the application.

### Traces do not reach the server at all

`--send-to-remote` has to point at the TCP socket used for CTF ingestion, that is `--tcp-server-port` (5000 by default):

```bash
west zpl-uart-capture /dev/ttyUSB0 115200 ./trace.ctf --send-to-remote 127.0.0.1:5000
```

Sending the data to `--bt-port` (42674 by default) instead bypasses the trace handler - this port is used internally between the server and the `libbtrace` live plugin.

### Layer profiling events are missing or appear to last forever in live mode only

Delayed emission makes the trace stream non-chronological, and the live pipeline renders the events as they arrive, dropping the ones older than the newest event already displayed for a given thread.
Offline conversion sorts the whole trace, so the same run visualized from a file is complete.

Disable `CONFIG_ZPL_TFLM_PROFILER_DELAYED_EMISSION` or `CONFIG_ZPL_TVM_PROFILER_DELAYED_EMISSION` when using live tracing.
