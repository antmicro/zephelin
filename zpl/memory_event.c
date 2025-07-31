/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/tracing/tracing_format.h>

#include <zpl/memory_event.h>

void zpl_emit_memory_for_thread_event(enum zpl_memory_region memory_region, uintptr_t memory_addr, uint32_t used_memory, uint32_t unused_memory, uint32_t for_thread_id)
{
#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
	uint32_t cycles = k_cycle_get_32();

	zpl_memory_event_t memory_event = {
		.timestamp = k_cyc_to_ns_floor64(cycles),
		.id = ZPL_MEMORY_EVENT,
		.memory_region = memory_region,
		.memory_addr = memory_addr,
		.used = used_memory,
		.unused = unused_memory,
		.for_thread_id = for_thread_id,
	};

	tracing_format_raw_data(
		(uint8_t *)&memory_event, sizeof(zpl_memory_event_t)
	);
#elif defined(CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT)
	TRACING_STRING(
		 "zpl_memory_event %s (%#x) %uB %uB %u\n", zpl_memory_region_enum_to_string(memory_region), memory_addr, used_memory, unused_memory, for_thread_id
	);
#endif /* CONFIG_ZPL_TRACE_FORMAT_* */
}

void zpl_emit_memory_event(enum zpl_memory_region memory_region, uintptr_t memory_addr, uint32_t used_memory, uint32_t unused_memory)
{
	zpl_emit_memory_for_thread_event(memory_region, memory_addr, used_memory, unused_memory, (uint32_t)NULL);
}

const char* zpl_memory_region_enum_to_string(enum zpl_memory_region memory_region)
{
	switch (memory_region) {
		case ZPL_STACK:
			return "stack";
		case ZPL_HEAP:
			return "heap";
		case ZPL_K_HEAP:
			return "k_heap";
		case ZPL_MEM_SLAB:
			return "mem_slab";
	}
	return "<unknown>";
}
