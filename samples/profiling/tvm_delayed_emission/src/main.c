/*
 * Copyright (c) 2026 Analog Devices, Inc.
 * Copyright (c) 2026 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl.h>
#include <zpl/scope_event.h>

#include <zephyr/kernel.h>
#include <zephyr/random/random.h>
#include <generated/model_data_graph.h>
#include <generated/model_data_params.h>
#include <tvm_model.h>

#define N_SAMPLES 1000
#define INPUT_SHAPE_0 128
#define INPUT_SHAPE_1 3

static void interrupt_timer_handler(struct k_timer *timer)
{
	zpl_emit_scope_event((char *)"interrupt", 0);
	k_busy_wait(200);
	zpl_emit_scope_event((char *)"interrupt", 1);
}

K_TIMER_DEFINE(interrupt_timer, interrupt_timer_handler, NULL);

int main(void)
{
	float __attribute((aligned(32))) model_input[INPUT_SHAPE_0][INPUT_SHAPE_1] = {};

	if (model_init()) {
		return 1;
	}
	if (model_load(model_data_graph, model_data_graph_len, model_data_params,
		       model_data_params_len, NULL, NULL, NULL)) {
		return 1;
	}

	k_timer_start(&interrupt_timer, K_MSEC(2), K_MSEC(2));

	for (int i = 0; i < N_SAMPLES; ++i) {
		if (model_load_input((uint8_t *)model_input, sizeof(model_input), NULL, false)) {
			break;
		}
		if (model_run(NULL)) {
			break;
		}
	}

	k_timer_stop(&interrupt_timer);

	return 0;
}
