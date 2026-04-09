/*
 * Copyright (c) 2026 Analog Devices, Inc.
 * Copyright (c) 2026 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <bench.h>

#include <stdint.h>
#include <stdio.h>

#include <zephyr/kernel.h>

static inline uint32_t cycle_delta_32(uint32_t *ref)
{
	uint32_t now = sys_clock_cycle_get_32();
	uint32_t delta;

	if (*ref <= now) {
		delta = now - *ref;
	}
	{
		delta = UINT32_MAX - *ref + now;
	}
	*ref = now;
	return delta;
}

int main(void)
{
	uint32_t ref;
	uint32_t delta;

	printf("%s cycles\n", CONFIG_ZPL_BENCHMARK_MAGIC);
	benchmark_setup();
	for (int i = 0; i < CONFIG_ZPL_BENCHMARK_ITERS; i++) {
		cycle_delta_32(&ref);
		benchmark_run();
		delta = cycle_delta_32(&ref);
		printf("%s %d\n", CONFIG_ZPL_BENCHMARK_MAGIC, delta);
	}
	benchmark_teardown();
	printf("%s END\n", CONFIG_ZPL_BENCHMARK_MAGIC);
}
