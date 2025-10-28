/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/instrumentation/instrumentation.h>


int __zpl_disable_instr(int __zpl_disable_instr_iter, bool __zpl_instr_enabled)
{
	if (!__zpl_instr_enabled) {
		return 1;
	}
	if (__zpl_disable_instr_iter == 0) {
		instr_disable();
	} else if (__zpl_disable_instr_iter == 1) {
		instr_enable();
	}
	return 1;
}
