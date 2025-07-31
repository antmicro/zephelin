/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/tflm_events.h>

#include <zephyr/kernel.h>
#include <zephyr/tracing/tracing_format.h>

#include <stdio.h>

void zpl_emit_tflm_enter_event(
	uint32_t cycles, uint16_t subgraph_idx, uint16_t op_idx, const char *tag,
	uint32_t arena_used_bytes, uint32_t arena_tail_usage)
{
#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
	zpl_tflm_enter_event_t zpl_tflm_enter_event = {
		.timestamp = k_cyc_to_ns_floor64(cycles),
		.id = ZPL_TFLM_ENTER_EVENT,
		.thread_id = (uint32_t)k_current_get(),
		.subgraph_idx = subgraph_idx,
		.op_idx = op_idx,
		.arena_used_bytes = arena_used_bytes,
		.arena_tail_usage = arena_tail_usage,
		.tag_len = CONFIG_ZPL_TRACE_CTF_MAX_STR_LEN,
	};
	snprintf(&(zpl_tflm_enter_event.tag[0]), CONFIG_ZPL_TRACE_CTF_MAX_STR_LEN, "%s", tag);

	tracing_format_raw_data(
		(uint8_t *)&zpl_tflm_enter_event, sizeof(zpl_tflm_enter_event)
	);
#elif defined(CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT)
	TRACING_STRING(
		"zpl_tflm_enter_event: subgraph_idx=%d op_idx=%d tag=%s "
		"arena_used_bytes=%d arena_tail_usage=%d\n",
		subgraph_idx, op_idx, tag, arena_used_bytes, arena_tail_usage);
#endif /* CONFIG_ZPL_TRACE_FORMAT_* */
}

void zpl_emit_tflm_exit_event(
	uint32_t cycles, uint16_t subgraph_idx, uint16_t op_idx, const char *tag,
	uint32_t arena_used_bytes, uint32_t arena_tail_usage)
{
#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
	zpl_tflm_exit_event_t zpl_tflm_exit_event = {
		.timestamp = k_cyc_to_ns_floor64(cycles),
		.id = ZPL_TFLM_EXIT_EVENT,
		.thread_id = (uint32_t)k_current_get(),
		.subgraph_idx = subgraph_idx,
		.op_idx = op_idx,
		.arena_used_bytes = arena_used_bytes,
		.arena_tail_usage = arena_tail_usage,
		.tag_len = CONFIG_ZPL_TRACE_CTF_MAX_STR_LEN,
	};
	snprintf(&(zpl_tflm_exit_event.tag[0]), CONFIG_ZPL_TRACE_CTF_MAX_STR_LEN, "%s", tag);

	tracing_format_raw_data(
		(uint8_t *)&zpl_tflm_exit_event, sizeof(zpl_tflm_exit_event)
	);
#elif defined(CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT)
	TRACING_STRING(
		"zpl_tflm_exit_event: subgraph_idx=%d op_idx=%d tag=%s "
		"arena_used_bytes=%d arena_tail_usage=%d\n",
		subgraph_idx, op_idx, tag, arena_used_bytes, arena_tail_usage);
#endif /* CONFIG_ZPL_TRACE_FORMAT_* */
}
