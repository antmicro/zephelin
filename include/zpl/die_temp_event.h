/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef ZPL_DIE_TEMP_EVENT_H_
#define ZPL_DIE_TEMP_EVENT_H_

/**
 * DIE temperature profiling.
 */

#include <stdint.h>

#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
/* DIE temp event ID */
#define ZPL_DIE_TEMP_EVENT 0xC1

/**
 * DIE temperature event structure.
 */
typedef struct __packed {
	uint32_t timestamp;
	uint8_t id;
	uint16_t sensor_count;
	float die_temp[CONFIG_ZPL_DIE_TEMP_PROFILING_SENSORS_COUNT];
} zpl_die_temp_event_t;
#endif /* defined(CONFIG_ZPL_TRACE_FORMAT_CTF) */

/**
 * Emits DIE temperature event.
 */
void zpl_emit_die_temp_event(void);

#endif /* ZPL_DIE_TEMP_EVENT_H_ */
