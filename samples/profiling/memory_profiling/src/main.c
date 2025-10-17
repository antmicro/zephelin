/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/sys/printk.h>
#include <zephyr/kernel.h>
#include <stdlib.h>
#include <zpl.h>
#include <zpl/configuration.h>

K_MEM_SLAB_DEFINE(test_mem_slab, 256, 32, 4);
K_HEAP_DEFINE(test_k_heap, 1024);

void recursive_function(int counter)
{
	char *block_ptr;

	if (k_mem_slab_alloc(&test_mem_slab, (void **)&block_ptr, K_MSEC(100)) == 0) {
		memset(block_ptr, 0, 100);
	}

	int *k_heap_variable = k_heap_alloc(&test_k_heap, 7, K_MSEC(100));
	int *heap_variable = k_malloc(sizeof(int) * 5);
	int *stdlib_malloc_test = malloc(sizeof(int) * 512);

	stdlib_malloc_test[0] = 5;

	sys_trace_named_event("counter", counter, 0);
	if (counter > 0) {
#ifdef CONFIG_ZPL_SAMPLE_RUNTIME_CONF_PROFILING
		if (counter == 4) {
			ZPL_CONF_SET(memory_profiler, true);
		} else if (counter == 2) {
			ZPL_CONF_SET(memory_profiler, false);
		}
#endif /* CONFIG_ZPL_SAMPLE_RUNTIME_CONF_PROFILING */
		k_msleep(200);
		recursive_function(counter - 1);
	}
	free(stdlib_malloc_test);
	k_free(heap_variable);
	k_heap_free(&test_k_heap, k_heap_variable);
	k_mem_slab_free(&test_mem_slab, block_ptr);
}

int main(void)
{
#ifdef CONFIG_ZPL_SAMPLE_RUNTIME_CONF_PROFILING
	ZPL_CONF_SET(memory_profiler, false);
#endif /* CONFIG_ZPL_SAMPLE_RUNTIME_CONF_PROFILING */
	zpl_init();
	recursive_function(5);
	k_msleep(5000);
#ifdef CONFIG_ZPL_SAMPLE_RUNTIME_CONF_PROFILING
	ZPL_CONF_SET(memory_profiler, true);
#endif /* CONFIG_ZPL_SAMPLE_RUNTIME_CONF_PROFILING */
	k_msleep(200);
	return 0;
}
