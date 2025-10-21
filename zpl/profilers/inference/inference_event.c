/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/inference_event.h>

#include <zephyr/kernel.h>
#include <zephyr/tracing/tracing_format.h>

#include <zpl/time.h>

void zpl_inference_enter(uint32_t model_id)
{
#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
	int key = irq_lock();
	zpl_inference_event_t zpl_inference_enter_event = {
		.timestamp = k_cyc_to_ns_floor64(soft_cycle_get_64()),
		.id = ZPL_INFERENCE_ENTER_EVENT,
		.cpu_id = arch_curr_cpu()->id,
		.thread_id = (uint32_t)k_current_get(),
		.stream_id = 0,
		.packet_size = sizeof(zpl_inference_event_t) * 8,
		.model_id = model_id,
	};

	tracing_format_raw_data(
		(uint8_t *)&zpl_inference_enter_event, sizeof(zpl_inference_event_t)
	);
	irq_unlock(key);
#elif defined(CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT)
	TRACING_STRING("%s: model_id=0x%x\n", __func__, model_id);
#endif /* CONFIG_ZPL_TRACE_FORMAT_* */
}

void zpl_inference_exit(uint32_t model_id)
{
#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
	int key = irq_lock();
	zpl_inference_event_t zpl_inference_exit_event = {
		.timestamp = k_cyc_to_ns_floor64(soft_cycle_get_64()),
		.id = ZPL_INFERENCE_EXIT_EVENT,
		.cpu_id = arch_curr_cpu()->id,
		.thread_id = (uint32_t)k_current_get(),
		.stream_id = 0,
		.packet_size = sizeof(zpl_inference_event_t) * 8,
		.model_id = model_id,
	};

	tracing_format_raw_data(
		(uint8_t *)&zpl_inference_exit_event, sizeof(zpl_inference_event_t)
	);
	irq_unlock(key);
#elif defined(CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT)
	TRACING_STRING("%s: model_id=0x%x\n", __func__, model_id);
#endif /* CONFIG_ZPL_TRACE_FORMAT_* */
}
