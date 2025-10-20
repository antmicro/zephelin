/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "tvm/runtime/c_runtime_api.h"
#include "tvm/runtime/crt/graph_executor.h"
#include "tvm/runtime/crt/internal/graph_executor/graph_executor.h"
#include <stdlib.h>
#include <zpl.h>

#include <zephyr/kernel.h>
#include <zephyr/random/random.h>
#include <generated/model_data_graph.h>
#include <generated/model_data_params.h>
#include <generated/model_data_int8_graph.h>
#include <generated/model_data_int8_params.h>
#include <model.h>

#define N_SAMPLES 10
#define INPUT_SHAPE_0 128
#define INPUT_SHAPE_1 3
#define INPUT_MIN_VAL -2040.0f
#define INPUT_MAX_VAL 2040.0f

#define TWO_PI      (2.0f * 3.14159265359f)
#define INPUT_SCALE 0.024573976173996925f
#define INPUT_ZERO  -128

void rand_input(float model_input[][INPUT_SHAPE_1]);

int main(void)
{
	int status = 0;
	float __attribute((aligned(32))) model_input[INPUT_SHAPE_0][INPUT_SHAPE_1];
	int8_t model_int8_input;

	zpl_init();

	status = model_init();
	if (status) {
		printk("Model init failed %d\n", status);
		return 1;
	}

	TVMGraphExecutor *executor = malloc(sizeof(TVMGraphExecutor));
	TVMGraphExecutor *executor_quantized = malloc(sizeof(TVMGraphExecutor));
	TVMModuleHandle handle = NULL, handle_quantized = NULL;

	status = model_load(model_data_graph, model_data_graph_len, model_data_params, model_data_params_len, &executor, &handle, false);
	if (status) {
		printk("Model load failed %d\n", status);
		return 1;
	}

	status = model_load(model_data_int8_graph, model_data_int8_graph_len, model_data_int8_params, model_data_int8_params_len, &executor_quantized, &handle_quantized, true);
	if (status) {
		printk("Quantized model load failed %d\n", status);
		return 1;
	}

	for (int batch_index = 0; batch_index < N_SAMPLES; ++batch_index) {
		/* magic-wand model */
		rand_input(model_input);
		status = model_load_input((uint8_t *)model_input, sizeof(float) * INPUT_SHAPE_0 * INPUT_SHAPE_1, executor, false);
		if (status) {
			printk("Model load input failed %d\n", status);
			break;
		}

		status = model_run(executor);
		if (status) {
			printk("Model run failed %d\n", status);
			break;
		}

		/* sine model */
		model_int8_input = ((TWO_PI * (float)sys_rand32_get() / (float)0xFFFFFFFF) / INPUT_SCALE) + INPUT_ZERO;

		status = model_load_input((uint8_t *)&model_int8_input, sizeof(int8_t), executor_quantized, true);
		if (status) {
			printk("Model load input failed %d\n", status);
			break;
		}

		status = model_run(executor_quantized);
		if (status) {
			printk("Model run failed %d\n", status);
			break;
		}
	}

	free(executor);
	free(executor_quantized);

	return 0;
}

void rand_input(float model_input[][INPUT_SHAPE_1])
{
	for (int i = 0; i < INPUT_SHAPE_0; ++i) {
		for (int j = 0; j < INPUT_SHAPE_1; ++j) {
			model_input[i][j] = (
				(INPUT_MAX_VAL - INPUT_MIN_VAL) * (float)sys_rand32_get() / (float)0xFFFFFFFF
			) + INPUT_MIN_VAL;
		}
	}
}
