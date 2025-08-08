/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl.h>
#include <zpl/tflm_event.h>
#include <zephyr/kernel.h>

int main(void)
{
	const char *tflm_op_tag = "TFLM_OP";

	zpl_init();

	zpl_emit_tflm_enter_event(k_cycle_get_32(), 0, 0, tflm_op_tag, 0, 1);
	zpl_emit_tflm_exit_event(k_cycle_get_32(), 0, 0, tflm_op_tag, 2, 3);

	return 0;
}
