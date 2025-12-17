/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef ZPL_SCOPE_EVENT_H_
#define ZPL_SCOPE_EVENT_H_

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ZPL_SCOPE_ENTER_EVENT 0x109
#define ZPL_SCOPE_EXIT_EVENT 0x10A
#define ZPL_MAX_SCOPE_NAME_LENGTH 30

typedef struct __packed {
	uint16_t stream_id;
	uint16_t packet_size;
	uint64_t timestamp;
	uint16_t id;
	uint8_t cpu_id;
	uint32_t thread_id;
	uint16_t scope_name_len;
	uint8_t scope_name[ZPL_MAX_SCOPE_NAME_LENGTH + 1];
	uint64_t cycles;
} zpl_scope_event_t;

void zpl_emit_scope_event(char *scope_name, uint8_t is_exit);

#ifdef __cplusplus
}
#endif

#endif /* ZPL_SCOPE_EVENT_H_ */
