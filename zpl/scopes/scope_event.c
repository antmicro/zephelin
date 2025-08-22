/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/scope_event.h>

#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/tracing/tracing_format.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(zpl_scope_event);

void zpl_emit_scope_event(char *scope_name, uint8_t is_exit)
{
#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
	if (strlen(scope_name) > ZPL_MAX_SCOPE_NAME_LENGTH) {
		LOG_WRN("Scope name \"%s\" is too long (%d > %d), might get truncated\n",
			scope_name, strlen(scope_name), ZPL_MAX_SCOPE_NAME_LENGTH);
	}

	uint32_t cycles = k_cycle_get_32();

	zpl_scope_event_t scope_event = {
		.id = (is_exit) ? ZPL_SCOPE_EXIT_EVENT : ZPL_SCOPE_ENTER_EVENT,
		.cycles = cycles,
		.timestamp = k_cyc_to_ns_floor64(cycles),
		.thread_id = (uint32_t)k_current_get(),
		.scope_name_len = ZPL_MAX_SCOPE_NAME_LENGTH + 1,
	};
	strncpy((char *)&scope_event.scope_name, scope_name, ZPL_MAX_SCOPE_NAME_LENGTH);
	tracing_format_raw_data((uint8_t *)&scope_event, sizeof(zpl_scope_event_t));
#elif defined(CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT)
	TRACING_STRING("zpl_scope_%s %lld %s %#x\n", is_exit ? "exit" : "enter",
			k_cyc_to_ns_floor64(k_cycle_get_32()), scope_name,
			(uint32_t)k_current_get());
#endif
}
