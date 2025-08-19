/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/memory_event.h>
#include <zpl/configuration.h>

#include <zephyr/kernel.h>
#include <zephyr/sys/sys_heap.h>
#include <zephyr/sys/iterable_sections.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(memory_profiler);

void zpl_profile_stack(const struct k_thread *thread, void *user_data)
{
	size_t unused;
	int err = k_thread_stack_space_get(thread, &unused);

	if (err) {
		LOG_ERR("Error getting thread stack space\n");
		return;
	}

	zpl_emit_memory_for_thread_event(
	  ZPL_STACK, thread->stack_info.start, thread->stack_info.size - unused, unused, (uint32_t)thread);
}

void zpl_profile_heap(void)
{
	struct sys_heap **ha;
	size_t i;
	struct sys_memory_stats stats;
	bool included_in_k_heap;

	for (i = 0; i < sys_heap_array_get(&ha); i++) {
		// Filter out heaps included in profile_k_heap
		included_in_k_heap = false;
		STRUCT_SECTION_FOREACH(k_heap, k_ha) {
			if ((uintptr_t)ha[i] == (uintptr_t)&k_ha->heap) {
				included_in_k_heap = true;
				break;
			}
		}
		if (included_in_k_heap) continue;

		sys_heap_runtime_stats_get(ha[i], &stats);
		zpl_emit_memory_event(ZPL_HEAP, (uintptr_t)ha[i], stats.allocated_bytes, stats.free_bytes);
	}
}

void zpl_profile_memory_slabs(void)
{
	STRUCT_SECTION_FOREACH(k_mem_slab, slab) {
		zpl_emit_memory_event(ZPL_MEM_SLAB, (uintptr_t)slab, slab->info.num_used * slab->info.block_size, slab->info.num_blocks * slab->info.block_size - slab->info.num_used * slab->info.block_size);
	}
}

void zpl_profile_k_heaps(void)
{
	struct sys_memory_stats stats;
	STRUCT_SECTION_FOREACH(k_heap, heap) {
		sys_heap_runtime_stats_get(&heap->heap, &stats);
		zpl_emit_memory_event(ZPL_K_HEAP, (uintptr_t)&heap->heap, stats.allocated_bytes, stats.free_bytes);
	}
}

void zpl_profile_memory(void)
{
	while (true) {
		ZPL_WAIT_FOR_CONF(mem_usage_trace);
		k_thread_foreach(zpl_profile_stack, NULL);
		zpl_profile_heap();
		zpl_profile_k_heaps();
		zpl_profile_memory_slabs();
		k_msleep(CONFIG_ZPL_MEMORY_PROFILING_INTERVAL);
	}
}

K_THREAD_DEFINE(zpl_mem_profiling,
				CONFIG_ZPL_MEMORY_PROFILING_THREAD_STACK_SIZE,
				zpl_profile_memory, NULL, NULL, NULL,
				CONFIG_ZPL_MEMORY_PROFILING_THREAD_PRIORITY,
				0, CONFIG_ZPL_MEMORY_PROFILING_THREAD_DELAY);
