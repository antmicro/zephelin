/*
 * Copyright (c) 2026 Analog Devices, Inc.
 * Copyright (c) 2026 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zpl.h>
#include <zpl/time.h>

#if defined(CONFIG_SENSOR_CLOCK)
#include <zephyr/drivers/sensor_clock.h>

static uint64_t cycles_get(void)
{
	uint64_t cycles;

	sensor_clock_get_cycles(&cycles);
	return cycles;
}

static uint64_t timestamp_get(uint64_t cycles)
{
	return sensor_clock_cycles_to_ns(cycles);
}
#elif defined(CONFIG_TIMING_FUNCTIONS) && !defined(CONFIG_INSTRUMENTATION)
#include <zephyr/timing/timing.h>
#include <zephyr/timing/types.h>

uint64_t cycles_get(void)
{
	timing_t start = 0;
	timing_t now = timing_counter_get();

	return timing_cycles_get(&start, &now);
}
static uint64_t timestamp_get(uint64_t cycles)
{
	return timing_cycles_to_ns(cycles);
}

int timing_init_sys(void)
{
	timing_init();
	timing_start();
	return 0;
}
SYS_INIT(timing_init_sys, APPLICATION, 0);
#else  /* CONFIG_SENSOR_CLOCK */
static uint64_t counter = 1;
static uint64_t cycles_get(void)
{
	return counter++;
}

static uint64_t timestamp_get(uint64_t cycles)
{
	return cycles;
}
#endif /* CONFIG_SENSOR_CLOCK */

#ifdef CONFIG_INSTRUMENTATION
#define sys_trace_named_event(fmt, ...)            \
	ZPL_DISABLE_INSTRUMENTATION {                  \
		printk(fmt" %llu\n", zpl_timestamp_get()); \
	}

#define PRINTK_SCOPE(name, value)                                                  \
	ZPL_DISABLE_INSTRUMENTATION { printk(name"_enter %llu\n", zpl_cycles_get()); } \
	value;                                                                         \
	ZPL_DISABLE_INSTRUMENTATION { printk(name"_exit %llu\n", zpl_cycles_get()); }
#else /* CONFIG_INSTRUMENTATION */
#define PRINTK_SCOPE(fmt, value) value
#endif /* CONFIG_INSTRUMENTATION */

static zpl_clock_t simple_clock = {
	.cycles_get = cycles_get,
	.timestamp_get = timestamp_get,
};

ZPL_CODE_SCOPE_DEFINE(nested_scope1, true);
ZPL_CODE_SCOPE_DEFINE(nested_scope2, true);

static __noinline void nested2(void)
{
	ZPL_MARK_CODE_SCOPE(nested_scope2) {
		PRINTK_SCOPE("nested2", sys_trace_named_event("top", 0, 0));
	}
}

__noinline void nested1(void)
{
	ZPL_MARK_CODE_SCOPE(nested_scope1) {
		PRINTK_SCOPE("nested2", nested2());
	}
}

int main(void)
{
	zpl_clock_set(simple_clock);
	zpl_init();

	k_sleep(K_MSEC(10));

	for (int i = 0; i < 10; i++) {
		sys_trace_named_event("tick", i, 0);
	}

	k_sleep(K_MSEC(10));

	nested1();

	return 0;
}
