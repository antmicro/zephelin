# Zeppelin

Zeppelin is implemented as a West module. The Zeppelin repository consists of
the following elements:
* Zeppelin proper
* Custom MAX78002 and MAX32690-based boards for testing purposes
* Samples, which also serve as integration tests
* Unit tests
* Patches to Zephyr RTOS

## Initializing the workspace

First, install West with `pip`, using the library `requirements.txt` file:
```bash
pip install -r requirements.txt
```

Next, initialize the workspace using West. To do that, issue the following command:
```bash
west init -l .
```

Now, prepare the project sources using the following commands:
```
west update
west patch apply
west zephyr-export
west packages pip --install
```

Now, install Renode:
```bash
export RENODE_VERSION="renode_1.15.3+20250320gitdbdcd8ae8_amd64.deb"
wget "https://dl.antmicro.com/projects/renode/builds/${RENODE_VERSION}" -O renode.deb
sudo dpkg -i renode.deb
```

Finally, download Zephyr SDK:
```bash
west sdk install
```

## Testing Zeppelin

To run unit and integration tests, use the following commands:
```bash
west twister -v -p max78002evkit_custom/max78002/m4 -p max32690fthr_custom/max32690/m4 -p qemu_cortex_m3 -T samples -T tests
```

## Using Zeppelin

Zeppelin can be enabled by y-selecting the `CONFIG_ZPL` symbol in the project
configuration file. To initialize Zeppelin in runtime, use the `zpl_init()` function
defined by the `zpl/lib.h` header. The user can enable various Zeppelin components
by using Kconfig and runtime configuration, as described in following sections.

### Configuration

The library can be configured both at build-time and runtime.
The description of how to configure the library and how to add new configurations is described in {doc}`configuration`.

### Tracing

To enable Zeppelin tracing support, the user should enable the `CONFIG_ZPL_TRACE`
symbol in Kconfig. The user can then select the following formats:
* Plaintext format, by y-selecting `CONFIG_TRACING_TEST`
* Common Trace Format (CTF), by y-selecting `CONFIG_TRACING_CTF`

The user can choose the tracing backend with the following Kconfig options:
* UART, by y-selecting `CONFIG_ZPL_TRACE_BACKEND_UART`
* USB, by y-selecting `CONFIG_ZPL_TRACE_BACKEND_USB`
* Debugger, by y-selecting `CONFIG_ZPL_TRACE_BACKEND_DEBUGGER`
* Renode's simulated trivial UART, by y-selecting `CONFIG_ZPL_TRACE_BACKEND_TRIVIAL_UART`

Depending on the tracing backend used, the following commands can be used for
trace capture.

#### west zpl-uart-capture

```bash
west zpl-uart-capture [-h] serial_port serial_baudrate output_path

Capture traces using UART. This command capures traces using the serial interface.

positional arguments:
  serial_port      Seral port
  serial_baudrate  Seral baudrate
  output_path      Capture output path

options:
  -h, --help       show this help message and exit
```

#### west zpl-usb-capture

```bash
west zpl-usb-capture [-h] [-t TIMEOUT] [-w] vendor_id product_id output_path

Capture traces using USB. This command capures traces using USB.

positional arguments:
  vendor_id             Vendor ID
  product_id            Product ID
  output_path           Capture output path

options:
  -h, --help            show this help message and exit
  -t, --timeout TIMEOUT
                        Timeout of the USB capture in seconds
  -w, --wait-for-device
                        When this flag is set, the command will wait for the device to connect
```

#### west zpl-gdb-capture

```bash
west zpl-gdb-capture [-h] elf_path output_path

Capture traces using GDB. This command captures traces using GDB from RAM using the `dump` command.

positional arguments:
  elf_path     Zephyr ELF path
  output_path  Capture output path

options:
  -h, --help   show this help message and exit
```

### Profiling tiers

The library supports three distinct profiling tiers, each offering a different balance of performance impact and tracing detail:
* `ZPL_TRACE_MINIMAL_MODE` - This mode provides extremely lightweight profiling with minimal overhead.
  It is designed for environments where performance is critical, and persistent trace data is not required.
  When enabled, it activates basic inference profiling (`ZPL_INFERENCE_PROFILING`) and memory usage tracing (`ZPL_MEMORY_USAGE_TRACE`) to give a high-level view of system behavior without introducing measurable latency.

* `ZPL_TRACE_LAYER_PROFILING_MODE` - This mode enables layer-level timing.
  It offers more granularity by tracking timing at individual model layers.

* `ZPL_TRACE_FULL_MODE` - This comprehensive profiling mode enables complete tracing.
  It includes all basic and layer-level profiling features, and additionally implies a wide array of kernel and runtime tracing subsystems.
  These include:
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

  This mode is suitable for in-depth debugging and performance analysis but incurs a higher runtime cost due to its extensive trace capture.

### Named events

To use named events, include the `zpl/lib.h` header, and use the
`sys_trace_named_event()` function to generate named events.

### Memory profiler

To use Zeppelin memory profiler, y-select the `CONFIG_ZPL_MEMORY_PROFILING` in
Kconfig. No further actions are needed in the application code to generate
memory profiling events in the generated trace. Memory profiling along with
memory events are described in {doc}`memory_profiling`.

### TLFM events

To use Zeppelin custom events with Tensorflow Lite Micro (TLFM), use the
`zpl_emit_tflm_begin_event()` and `zpl_emit_tflm_end_event()` functions
provided by `zpl/tflm_events.h`.
