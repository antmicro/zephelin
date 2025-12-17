/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef ZPL_CPU_LOAD_EVENT_H_
#define ZPL_CPU_LOAD_EVENT_H_

/**
 * CPU load profiling.
 */

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
/* CPU load event ID */
#define ZPL_CPU_LOAD_EVENT 0x107

/**
 * CPU load event structure.
 */
typedef struct __packed {
	uint16_t stream_id;
	uint16_t packet_size;
	uint64_t timestamp;
	uint16_t id;
	uint8_t cpu_id;
	uint16_t cpu_load; /* CPU load denoted by a number 0-1000 */
} zpl_cpu_load_event_t;
#endif /* defined(CONFIG_ZPL_TRACE_FORMAT_CTF) */

/**
 * Emits CPU load event.
 */
void zpl_emit_cpu_load_event(void);

#ifdef __cplusplus
}
#endif

#endif /* ZPL_CPU_LOAD_EVENT_H_ */
