/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef ZPL_TVM_EVENTS_H_
#define ZPL_TVM_EVENTS_H_

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
/* TVM events IDs */
#define ZPL_TVM_BEGIN_EVENT 0x102
#define ZPL_TVM_END_EVENT 0x103

typedef struct __packed {
	uint16_t stream_id;
	uint16_t packet_size;
	uint64_t timestamp;
	uint16_t id;
	uint8_t cpu_id;
	uint32_t thread_id;
	uint8_t op_idx;
	uint16_t tag_len;
	uint8_t tag[CONFIG_ZPL_TRACE_CTF_MAX_LONG_STR_LEN];
} zpl_tvm_event_t;
#endif /* defined(CONFIG_ZPL_TRACE_FORMAT_CTF) */

void zpl_emit_tvm_enter_event(uint64_t cycles, uint8_t op_idx, const char *tag);

void zpl_emit_tvm_exit_event(uint64_t cycles, uint8_t op_idx, const char *tag);

#ifdef __cplusplus
}
#endif

#endif /* ZPL_TVM_EVENTS_H_ */
