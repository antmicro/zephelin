/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/time.h>

#include <zephyr/kernel.h>

#ifdef CONFIG_TIMER_HAS_64BIT_CYCLE_COUNTER
inline uint64_t soft_cycle_get_64(void)
{
	return sys_clock_cycle_get_64();
}
#else /* CONFIG_TIMER_HAS_64BIT_CYCLE_COUNTER */
uint64_t soft_cycle_get_64(void)
{
	static uint32_t overflows;
	static uint32_t prev_clk;

	uint32_t clk = k_cycle_get_32();

	overflows += prev_clk > clk;
	prev_clk = clk;
	return (uint64_t)overflows << 32 | clk;
}
#endif /* CONFIG_TIMER_HAS_64BIT_CYCLE_COUNTER */
