/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/cpu_load_event.h>

#include <zephyr/kernel.h>
#include <zephyr/debug/cpu_load.h>
#include <zephyr/tracing/tracing_format.h>

void zpl_emit_cpu_load_event(void)
{
	int cpu_load = cpu_load_get(true);

#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
	zpl_cpu_load_event_t zpl_cpu_load_event = {
		.timestamp = k_cyc_to_ns_floor64(k_cycle_get_32()),
		.id = ZPL_CPU_LOAD_EVENT,
		.cpu_load = cpu_load,
	};
	tracing_format_raw_data(
		(uint8_t *)&zpl_cpu_load_event, sizeof(zpl_cpu_load_event_t)
	);
#elif defined(CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT)
	TRACING_STRING("zpl_cpu_load_event: cpu_load=%d.%d%\n", cpu_load / 10, cpu_load % 10);
#endif /* CONFIG_ZPL_TRACE_FORMAT_* */
}

#ifdef CONFIG_ZPL_CPU_LOAD_TRACE

static void zpl_profile_cpu_load(void)
{
	while (true) {
		zpl_emit_cpu_load_event();
		k_msleep(CONFIG_ZPL_CPU_LOAD_PROFILING_INTERVAL);
	}
}

K_THREAD_DEFINE(zpl_cpu_load_profiling,
				CONFIG_ZPL_CPU_LOAD_PROFILING_THREAD_STACK_SIZE,
				zpl_profile_cpu_load, NULL, NULL, NULL,
				CONFIG_ZPL_CPU_LOAD_PROFILING_THREAD_PRIORITY,
				0, CONFIG_ZPL_CPU_LOAD_PROFILING_THREAD_DELAY);

#endif /* CONFIG_ZPL_CPU_LOAD_TRACE */
