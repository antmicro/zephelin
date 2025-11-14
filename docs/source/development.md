# Zephelin's developer guidelines

This chapter covers and links to resources and paths related to development and enhancing Zephelin library.

## General Zephyr development guidelines

With regard to code styling and configuration, this project follows Zephyr's development guidelines and linting rules - for more details check [General guidelines for Zephyr](https://docs.zephyrproject.org/latest/contribute/index.html).

For setting up development environment check the [Zephelin project introduction](library).

## Adding build-time and runtime configurations for Zephelin

Instructions on how to introduce new configuration options available either during build time or when the application is running can be found in [Adding new configurations](adding-new-configurations).

## Adding support for new AI inference libraries

Details on how to introduce support for new AI runtimes is explained in detail in a separate chapter - [Adding support for new AI inference libraries](new_runtime).

(adding-new-trace-backends)=
## Adding support for new trace backends

Existing implementations of backends can be found in {zpl_repo}`zpl/backends` and in [zephyr/subsys/tracing](https://github.com/zephyrproject-rtos/zephyr/tree/main/subsys/tracing)

To allow sending trace data through a new backend, in the simplest case you need to implement two methods:

* A method for initializing the backend, e.g.:
  ```c
  static void tracing_backend_custom_impl_init(void);
  ```
* A method for yielding trace data to implemented communication method, e.g.:
  ```c
  static void tracing_backend_custom_impl_output(const struct tracing_backend *backend, uint8_t *data, uint32_t length);
  ```

Then, you need to prepare a `tracing_backend_api` struct with the above methods (see [zephyr/subsys/tracing/include/tracing_backend.h](https://github.com/zephyrproject-rtos/zephyr/blob/main/subsys/tracing/include/tracing_backend.h) for more details):

```c
const struct tracing_backend_api tracing_backend_custom_impl_api = {
    .init = tracing_backend_custom_impl_init,
    .output = tracing_backend_custom_impl_output
};
```

And register the backend using `TRACING_BACKEND_DEFINE` from [zephyr/subsys/tracing/include/tracing_backend.h](https://github.com/zephyrproject-rtos/zephyr/blob/main/subsys/tracing/include/tracing_backend.h):

```c
TRACING_BACKEND_DEFINE(tracing_backend_custom_impl, tracing_backend_custom_impl_api);
```

In the end, you can define a corresponding entry in {zpl_repo}`zpl/backends/Kconfig`, e.g. `CONFIG_ZPL_TRACE_BACKEND_UART` and configure build for the backend in {zpl_repo}`zpl/backends/CMakeLists.txt`:

```cmake
zephyr_library_sources_ifdef(CONFIG_ZPL_TRACE_BACKEND_UART custom_impl_backend.c)
```

The Renode Trivial UART backend ({zpl_repo}`zpl/backends/trivial_uart_backend.c`) can be used as a simple example of adding new backends in Zephelin.

## Adding support for tracing new data sources in Zephelin

Existing implementations of tracing specific data sources (CPU load, temperature, ...) can be found in {zpl_repo}`zpl/profilers`.

Implementation of tracing custom data in the application boils down to:

* Defining a new event type
* Defining a function for reading data and creating an event and printing it
* (depending on source type) Setting up a separate thread to collect traces

Let's discuss how this can be implemented on an example of CPU load.

First of, you need to define an event that will store the collected sample - a packed `struct` can be defined in a dedicated header in {zpl_repo}`include/zpl`:

```c
#ifdef __cplusplus
extern "C" {
#endif

#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
/* CPU load event ID */
#define ZPL_CPU_LOAD_EVENT 0xC0

/**
 * CPU load event structure.
 */
typedef struct __packed {
	uint16_t stream_id;
	uint16_t packet_size;
	uint64_t timestamp;
	uint8_t id;
	uint8_t cpu_id;
	uint16_t cpu_load; /* CPU load denoted by a number 0-1000 */
} zpl_cpu_load_event_t;
#endif /* defined(CONFIG_ZPL_TRACE_FORMAT_CTF) */

/**
 * Emits CPU load event.
 */
void zpl_emit_cpu_load_event(void);

#ifdef __cplusplus
}
#endif
```

The `ZPL_CPU_LOAD_EVENT 0xC0` is a unique event ID - for the list of existing events' IDs check either {zpl_repo}`zpl/metadata` events' metadata file or in [Events documentation](trace-events), which describe events for both CTF and TEF format.
The `zpl_cpu_load_event_t` structure holds:

* `stream_id` - ID of the stream for data, currently `1` is used for AI runtimes and `0` for the remaining events
* `cpu_id` - ID of the CPU on which the event is collected
* `id` - ID of the event, in here it should be `ZPL_CPU_LOAD_EVENT`
* `timestamp` - timestamp for the event, in nanoseconds
* `packet_size` - size of the entire structure in bits
* event-specific data

The corresponding event entry needs to be created in the {zpl_repo}`zpl/metadata`:

```
event {
	stream_id = 0;
	name = zpl_cpu_load_event;
	id = 0xC0;
	fields := struct {
		uint8_t cpu_id;
		uint16_t cpu_load;
	};
};
```

Later, you need to implement a function for collecting the traces - it needs to support either CTF or plain text format, and needs to be configurable at compile time or during execution.
Implementation may look like so:

```c
void zpl_emit_cpu_load_event(void)
{
	// do nothing if cpu_load is disabled
	ZPL_CONF_RETURN_IF_DISABLED(cpu_load);
	int cpu_load = cpu_load_get(true);

#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
	// Yielding CPU load data in CTF format
	// Acquire lock to avoid parallel emitting
	int key = irq_lock();
	// Define and fill the event
	zpl_cpu_load_event_t zpl_cpu_load_event = {
		.timestamp = k_cyc_to_ns_floor64(soft_cycle_get_64()),
		.id = ZPL_CPU_LOAD_EVENT,
		.cpu_id = arch_curr_cpu()->id,
		.cpu_load = cpu_load,
		.stream_id = 0,
		.packet_size = sizeof(zpl_cpu_load_event_t) * 8,
	};
	// Emit the event
	tracing_format_raw_data(
		(uint8_t *)&zpl_cpu_load_event, sizeof(zpl_cpu_load_event_t)
	);
	irq_unlock(key);
#elif defined(CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT)
	// Yielding CPU load data in plain text format
	TRACING_STRING("zpl_cpu_load_event: cpu_load=%d.%d%\n", cpu_load / 10, cpu_load % 10);
#endif /* CONFIG_ZPL_TRACE_FORMAT_* */
}
```

The steps for the code are described in the comments.
`ZPL_CONF_RETURN_IF_DISABLED` is described in [Zephelin configuration chapter](return-if-disabled).

In the end, you can implement the thread that will periodically read the CPU load and emit the event.

```c
static void zpl_profile_cpu_load(void)
{
	while (true) {
		ZPL_CONF_WAIT(cpu_load_profiler);
		zpl_emit_cpu_load_event();
		k_msleep(CONFIG_ZPL_CPU_LOAD_PROFILING_INTERVAL);
	}
}

K_THREAD_DEFINE(zpl_cpu_load_profiling,
		CONFIG_ZPL_CPU_LOAD_PROFILING_THREAD_STACK_SIZE,
		zpl_profile_cpu_load, NULL, NULL, NULL,
		CONFIG_ZPL_CPU_LOAD_PROFILING_THREAD_PRIORITY,
		0, CONFIG_ZPL_CPU_LOAD_PROFILING_THREAD_DELAY);
```

This will emit events either in text or CTF format.
The CTF traces later will be parsed by {zpl_repo}`scripts/ctf2tef.py` script to generate TEF traces for Trace Viewer to obtain - check {doc}`ctf_to_tef` for more details.
