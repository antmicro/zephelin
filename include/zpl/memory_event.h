/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef ZEPHYR_PROFILING_LIB_MEMORY_EVENT_H_
#define ZEPHYR_PROFILING_LIB_MEMORY_EVENT_H_

#include <stdint.h>

#define ZPL_MEMORY_EVENT 0xEE

enum zpl_memory_region {
	ZPL_STACK,
	ZPL_HEAP,
	ZPL_K_HEAP,
	ZPL_MEM_SLAB,
};

typedef struct __packed {
	uint32_t timestamp;
	uint8_t id;
	enum zpl_memory_region memory_region;
	uintptr_t memory_addr;
	uint32_t used;
	uint32_t unused;
	uint32_t for_thread_id;
} zpl_memory_event_t;

void zpl_emit_memory_event(enum zpl_memory_region memory_region, uintptr_t memory_addr, uint32_t used_memory, uint32_t unused_memory);
void zpl_emit_memory_for_thread_event(enum zpl_memory_region memory_region, uintptr_t memory_addr, uint32_t used_memory, uint32_t unused_memory, uint32_t for_thread_id);
const char* zpl_memory_region_enum_to_string(enum zpl_memory_region memory_region);

#endif /* ZEPHYR_PROFILING_LIB_MEMORY_EVENT_H_ */
