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

#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
/* Inference events IDs */
#define ZPL_INFERENCE_ENTER_EVENT 0xD0
#define ZPL_INFERENCE_EXIT_EVENT 0xD1

/**
 * Inference event structure.
 */
typedef struct __packed {
	uint32_t timestamp;
	uint8_t id;
	uint32_t thread_id;
} zpl_inference_event_t;
#endif /* defined(CONFIG_ZPL_TRACE_FORMAT_CTF) */

/**
 * Marks inference enter.
 */
void zpl_inference_enter(void);

/**
 * Marks inference exit.
 */
void zpl_inference_exit(void);

#endif /* ZPL_INFERENCE_EVENT_H_ */
