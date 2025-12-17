/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef ZPL_INFERENCE_EVENT_H_
#define ZPL_INFERENCE_EVENT_H_

/**
 * Inference duration profiling.
 */

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
/* Inference events IDs */
#define ZPL_INFERENCE_ENTER_EVENT 0x104
#define ZPL_INFERENCE_EXIT_EVENT 0x105

/**
 * Inference event structure.
 */
typedef struct __packed {
	uint16_t stream_id;
	uint16_t packet_size;
	uint64_t timestamp;
	uint16_t id;
	uint8_t cpu_id;
	uint32_t thread_id;
	uint32_t model_id;
} zpl_inference_event_t;
#endif /* defined(CONFIG_ZPL_TRACE_FORMAT_CTF) */

/**
 * Marks inference enter.
 */
void zpl_inference_enter(uint32_t model_id);

/**
 * Marks inference exit.
 */
void zpl_inference_exit(uint32_t model_id);

#ifdef __cplusplus
}
#endif

#endif /* ZPL_INFERENCE_EVENT_H_ */
