/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/inference_event.h>

#include <zephyr/kernel.h>
#include <zephyr/tracing/tracing_format.h>

void zpl_inference_enter(void)
{
#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
	zpl_inference_event_t zpl_inference_enter_event = {
		.timestamp = k_cyc_to_ns_floor64(k_cycle_get_32()),
		.id = ZPL_INFERENCE_ENTER_EVENT,
		.thread_id = (uint32_t)k_current_get(),
	};

	tracing_format_raw_data(
		(uint8_t *)&zpl_inference_enter_event, sizeof(zpl_inference_event_t)
	);
#elif defined(CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT)
	TRACING_STRING("%s:\n", __func__);
#endif /* CONFIG_ZPL_TRACE_FORMAT_* */
}

void zpl_inference_exit(void)
{
#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
	zpl_inference_event_t zpl_inference_exit_event = {
		.timestamp = k_cyc_to_ns_floor64(k_cycle_get_32()),
		.id = ZPL_INFERENCE_EXIT_EVENT,
		.thread_id = (uint32_t)k_current_get(),
	};

	tracing_format_raw_data(
		(uint8_t *)&zpl_inference_exit_event, sizeof(zpl_inference_event_t)
	);
#elif defined(CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT)
	TRACING_STRING("%s:\n", __func__);
#endif /* CONFIG_ZPL_TRACE_FORMAT_* */
}
