# Memory profiling

The memory profiling functionality allows tracing of different memory regions.
To use it, enable `CONFIG_ZPL_MEMORY_PROFILING` in the Kconfig.

## Memory types

The profiling tool currently supports the following memory regions in Zephyr:

* [Stack](https://docs.zephyrproject.org/latest/kernel/services/data_passing/stacks.html)
* [Heaps](https://docs.zephyrproject.org/latest/kernel/memory_management/heap.html)
* [k_heaps](https://docs.zephyrproject.org/latest/kernel/memory_management/heap.html)
* [Memory Slabs](https://docs.zephyrproject.org/latest/kernel/memory_management/slabs.html)

## Memory event

The memory tracing tool uses custom events.
Those events contain information about the memory regions at a point in time.

(memory-ctf)=
### Common Trace Format

The memory event is a packed structure, described below.
It contains information about:
* `timestamp` - the timestamp at which the event occurred
* `id` - id of the event defined as `0xEE`
* `memory_region` - the profiled memory region (stack, heap, etc.)
* `memory_addr` - memory address, which serves as memory region identifier
* `used`, `unused` - Used and unused number of bytes
* `for_thread_id` - ID of the thread associated with the memory region or 0 otherwise

```c
typedef struct __packed {
    uint32_t timestamp;
    uint8_t id;
    enum zpl_memory_region memory_region;
    uintptr_t memory_addr;
    uint32_t used;
    uint32_t unused;
    uint32_t for_thread_id;
} zpl_memory_event_t;
```

The available memory regions are defined as an enum:

```c
enum zpl_memory_region {
    ZPL_STACK = 0,
    ZPL_HEAP,
    ZPL_K_HEAP,
    ZPL_MEM_SLAB,
};
```

### Plaintext

When using a `CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT` format, the memory events are printed in plaintext.
The events contain the same information as in the CTF format, but in human readable form.
The example shown below, contains a series of memory events of different memory regions.

* `zpl_memory_event` - event name
* `stack`, `heap`, etc. - memory region
* `0x20011748` - memory address
* `80B 432B` - used and unused memory size (in order)
* `536936848` - thread ID

```
zpl_memory_event stack (0x20011748) 80B 432B 536936848
zpl_memory_event stack (0x20011348) 48B 976B 536936848
zpl_memory_event stack (0x20012148) 48B 272B 536937024
zpl_memory_event stack (0x20012288) 280B 744B 536937200
zpl_memory_event heap (0x20010048) 28B 164B 0
zpl_memory_event heap (0x2001005c) 12B 940B 0
zpl_memory_event heap (0x200106ac) 0B 47132B 0
zpl_memory_event k_heap (0x20010048) 28B 164B 0
zpl_memory_event k_heap (0x2001005c) 12B 940B 0
zpl_memory_event mem_slab (0x2001002c) 256B 7936B 0
```
