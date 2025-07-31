/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zpl/lib.h>

int main(void)
{
	zpl_init();

	for (int i = 0; i < 100; i++) {
		sys_trace_named_event("counter_value", i, 0);
		k_sleep(K_SECONDS(1));
	}

	return 0;
}
