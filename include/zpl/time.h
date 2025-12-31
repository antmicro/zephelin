/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef ZPL_TIME_H_
#define ZPL_TIME_H_

#include <zephyr/init.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Obtain the current cycle count.
 *
 * By default, this function uses clock provided by system timer driver. If the
 * 64 bit cycle counter is not supported, it uses 32 bit counter, it coerces the
 * result by counting integer overflows.
 *
 * @return The current cycle time.
 */
uint64_t zpl_cycles_get(void);

#ifndef CONFIG_ZPL_CONFIGURABLE_TIMESTAMP_CLOCK
/**
 * Obtain the current timestamp computed from clock cycles.
 *
 * @return The current timestamp.
 */
static inline uint64_t zpl_timestamp_get_from_cycles(uint64_t cycles)
{
	return k_cyc_to_ns_floor64(cycles);
}

/**
 * Obtain the current timestamp.
 *
 * @return The current timestamp.
 */
static inline uint64_t zpl_timestamp_get(void)
{
	return zpl_timestamp_get_from_cycles(zpl_cycles_get());
}
#else
/**
 * Timestamp clock configuration.
 */
typedef struct {
	/* Function to obtain current cycle count */
	uint64_t (*cycles_get)(void);
	/* Function to obtain current timestamp */
	uint64_t (*timestamp_get)(uint64_t cycles);
} zpl_clock_t;

/**
 * Set the global clock used for creating timestamps.
 *
 * If CONFIG_TRACING_CTF_CONFIGURABLE_TIMER is set, it also initializes tracing
 * timestamp function.
 *
 * @param clock Clock to be used.
 * @return 0 on success.
 */
int zpl_clock_set(zpl_clock_t clock);

/**
 * Obtain the current timestamp computed from clock cycles.
 *
 * @return The current timestamp.
 */
uint64_t zpl_timestamp_get_from_cycles(uint64_t cycles);

/**
 * Obtain the current timestamp.
 *
 * @return The current timestamp.
 */
uint64_t zpl_timestamp_get(void);
#endif

#ifdef __cplusplus
}
#endif

#endif /* ZPL_TIME_H_ */
