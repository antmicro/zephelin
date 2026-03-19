/*
 * Copyright (c) 2025-2026 Analog Devices, Inc.
 * Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/time.h>

#include <zephyr/kernel.h>
#include <zephyr/sys/util.h>
#include <zephyr/sys/time_units.h>
#include <zephyr/timing/timing.h>

#ifdef CONFIG_ZPL_CONFIGURABLE_TIMESTAMP_CLOCK
#define _CYCLE_GET
#else /* CONFIG_ZPL_CONFIGURABLE_TIMESTAMP_CLOCK */
#define _CYCLE_GET static inline
#endif /* CONFIG_ZPL_CONFIGURABLE_TIMESTAMP_CLOCK */

_CYCLE_GET uint64_t soft_cycle_get_64(void)
{
	static timing_t bigbang;
	timing_t now;

	now = timing_counter_get();
	return timing_cycles_get(&bigbang, &now);
}

#undef _CYCLE_GET

#ifdef CONFIG_ZPL_CONFIGURABLE_TIMESTAMP_CLOCK
#include <tracing_core.h>
static uint64_t cyc_to_ns_floor64(uint64_t cycles)
{
	return timing_cycles_to_ns(cycles);
}

static zpl_clock_t zpl_clock = {
	.cycles_get = soft_cycle_get_64,
	.timestamp_get = cyc_to_ns_floor64,
};

int zpl_clock_set(zpl_clock_t clock)
{
	zpl_clock = clock;
	int status = 0;
#ifdef CONFIG_TRACING_CTF_CONFIGURABLE_TIMER
	status = tracing_set_ctf_timestamp_func(zpl_timestamp_get);
#endif /* CONFIG_TRACING_CTF_CONFIGURABLE_TIMER */
	return status;
}

uint64_t zpl_cycles_get(void)
{
	return zpl_clock.cycles_get();
}

uint64_t zpl_timestamp_get_from_cycles(uint64_t cycles)
{
	return zpl_clock.timestamp_get(cycles);
}

uint64_t zpl_timestamp_get(void)
{
	return zpl_clock.timestamp_get(zpl_clock.cycles_get());
}
#else /* CONFIG_ZPL_CONFIGURABLE_TIMESTAMP_CLOCK */
uint64_t zpl_cycles_get(void)
{
	return soft_cycle_get_64();
}
#endif /* CONFIG_ZPL_CONFIGURABLE_TIMESTAMP_CLOCK */
