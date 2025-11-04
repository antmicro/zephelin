/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "tvm/runtime/c_runtime_api.h"
#include "tvm/runtime/crt/graph_executor.h"
#include "tvm/runtime/crt/internal/graph_executor/graph_executor.h"
#include "zephyr/irq.h"
#include <zpl.h>

#include <zephyr/kernel.h>
#include <zephyr/random/random.h>
#include <generated/model_data_int8_graph.h>
#include <generated/model_data_int8_params.h>
#include <tvm_model.h>
#include <sine.h>

#define N_SAMPLES     10
#define INPUT_MIN_VAL 0.0f
#define INPUT_MAX_VAL (2.0f * 3.14159265359f)

#define INPUT_SCALE 0.024573976173996925f
#define INPUT_ZERO  -128

ZPL_CODE_SCOPE_DEFINE(prepare_model, true);

void rand_input(float *model_input);

int main(void)
{
	int status = 0;
	float __attribute((aligned(32))) model_input;
	TVMGraphExecutor *executor_quantized = malloc(sizeof(TVMGraphExecutor));
	TVMModuleHandle handle_quantized = NULL;

#ifdef CONFIG_ZPL
	zpl_init();
#endif

	ZPL_MARK_CODE_SCOPE(prepare_model) {
		status = model_init();
		if (status) {
			printk("Model init failed %d\n", status);
			return 1;
		}

		status = model_load(model_data_int8_graph, model_data_int8_graph_len, model_data_int8_params, model_data_int8_params_len, &executor_quantized, &handle_quantized, TVMQuantizedLibEntryPoint());
		if (status) {
			printk("Model load failed %d\n", status);
			return 1;
		}
	}

	unsigned int lock_key;
	for (int batch_index = 0; batch_index < N_SAMPLES; ++batch_index) {
		rand_input(&model_input);
		status = model_load_input((uint8_t *)&model_input, sizeof(int8_t), executor_quantized, true);
		if (status) {
			printk("Model load input failed %d\n", status);
			break;
		}

		lock_key = irq_lock();
		status = model_run(executor_quantized);
		irq_unlock(lock_key);
		if (status) {
			printk("Model run failed %d\n", status);
			break;
		}
	}

	free(executor_quantized);
	return 0;
}

void rand_input(float *model_input)
{
	*model_input =
		((INPUT_MAX_VAL - INPUT_MIN_VAL) * (float)sys_rand32_get() / (float)0xFFFFFFFF) +
		INPUT_MIN_VAL;
}
