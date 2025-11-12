/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef ZPL_DIE_TEMP_EVENT_H_
#define ZPL_DIE_TEMP_EVENT_H_

/**
 * Die temperature profiling.
 */

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
/* Die temp event ID */
#define ZPL_DIE_TEMP_EVENT 0xC1

/**
 * Die temperature event structure.
 */
typedef struct __packed {
	uint16_t stream_id;
	uint16_t packet_size;
	uint64_t timestamp;
	uint8_t id;
	uint16_t sensor_count;
	float die_temp[CONFIG_ZPL_DIE_TEMP_PROFILING_SENSORS_COUNT];
} zpl_die_temp_event_t;
#endif /* defined(CONFIG_ZPL_TRACE_FORMAT_CTF) */

/**
 * Emits Die temperature event.
 */
void zpl_emit_die_temp_event(void);

#ifdef __cplusplus
}
#endif

#endif /* ZPL_DIE_TEMP_EVENT_H_ */
