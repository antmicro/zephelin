/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

extern "C" {
#include "tvm/runtime/c_runtime_api.h"
#include "tvm/runtime/crt/graph_executor.h"
#include "tvm/runtime/crt/internal/graph_executor/graph_executor.h"
#include <tvm_model.h>

#include <zpl.h>
#include <zephyr/kernel.h>
#include <zephyr/random/random.h>

/* microTVM */
#include <sine.h>
#include <sine2.h>
#include <generated/model_data_int8_graph.h>
#include <generated/model_data_int8_params.h>
#include <generated/model_data_sine2_graph.h>
#include <generated/model_data_sine2_params.h>
/* TFLM */
#include <generated/model0_data.h>
#include <generated/model1_data.h>
}

#include <tflm_model.h>

#define N_SAMPLES 10
#define INPUT0_SHAPE_0 128
#define INPUT0_SHAPE_1 3
#define INPUT0_MIN_VAL -2040.0f
#define INPUT0_MAX_VAL 2040.0f

#define INPUT1_MIN_VAL 0.0f
#define INPUT1_MAX_VAL (2.0f * 3.14159265359f)
#define INPUT1_SCALE 0.024573976173996925f
#define INPUT1_ZERO  -128

ZPL_CODE_SCOPE_DEFINE(tflm_init, true);
ZPL_CODE_SCOPE_DEFINE(tflm_model_load, true);
ZPL_CODE_SCOPE_DEFINE(tvm_init, true);
ZPL_CODE_SCOPE_DEFINE(tvm_model_load, true);

void rand_input0(float model_input[][INPUT0_SHAPE_1]);
void rand_input1(float *model_input);

int main(void)
{
	float model1_input;
	uint8_t model1_input_q;
	tflite::MicroInterpreter* interpreters[] = {nullptr, nullptr};

	TVMGraphExecutor* executors[2] = {(TVMGraphExecutor*) malloc(sizeof(TVMGraphExecutor)), (TVMGraphExecutor*) malloc(sizeof(TVMGraphExecutor))};
	TVMModuleHandle handle_quantized = NULL, handle_sine2 = NULL;
	int8_t model_int8_input;

	int status = 0;

	zpl_init();

	#ifdef CONFIG_ZPL_TRACE_BACKEND_USB
	k_sleep(K_MSEC(500));
	#endif

	ZPL_MARK_CODE_SCOPE(tflm_init) {
		tflm::model_init();
	}

	ZPL_MARK_CODE_SCOPE(tflm_model_load) {
		status = tflm::model_load(model0_data, interpreters[0], 15500);
		if (status) {
			printk("TFLM model 0 load failed %d\n", status);
			return 1;
		}
	}
	ZPL_MARK_CODE_SCOPE(tflm_model_load) {
		status = tflm::model_load(model1_data, interpreters[1]);
		if (status) {
			printk("TFLM model 1 load failed %d\n", status);
			return 1;
		}
	}

	ZPL_MARK_CODE_SCOPE(tvm_init) {
		model_init();
	}

	ZPL_MARK_CODE_SCOPE(tvm_model_load) {
		status = model_load(model_data_int8_graph, model_data_int8_graph_len, model_data_int8_params, model_data_int8_params_len, &executors[0], &handle_quantized, TVMQuantizedLibEntryPoint());
		if (status) {
			printk("TVM quantized model load failed %d\n", status);
			return 1;
		}
	}
	ZPL_MARK_CODE_SCOPE(tvm_model_load) {
		status = model_load(model_data_sine2_graph, model_data_sine2_graph_len, model_data_sine2_params, model_data_sine2_params_len, &executors[1], &handle_sine2, TVMSine2LibEntryPoint());
		if (status) {
			printk("TVM sine2 load failed %d\n", status);
			return 1;
		}
	}

	for (short i = 0; i < N_SAMPLES; ++i) {

		for (short j = 0; j < 2; ++j) {
			rand_input1(&model1_input);
			model1_input_q = (model1_input / INPUT1_SCALE) + INPUT1_ZERO;

			status = tflm::model_load_input(interpreters[j], (uint8_t *)&model1_input_q,
					sizeof(uint8_t));
			if (status) {
				printk("Model %d load input failed %d\n", j, status);
				break;
			}

			status = tflm::model_run(interpreters[j]);
			if (status) {
				printk("Model %d run failed %d\n", j, status);
				break;
			}
		}

		for (short j = 0; j < 2; ++j) {
			rand_input1(&model1_input);
			model1_input_q = (model1_input / INPUT1_SCALE) + INPUT1_ZERO;

			status = model_load_input((uint8_t *)&model_int8_input, sizeof(int8_t), executors[j], true);
			if (status) {
				printk("Model load input failed %d\n", status);
				break;
			}

			status = model_run(executors[j]);
			if (status) {
				printk("Model run failed %d\n", status);
				break;
			}
		}
	}

	free(executors[0]);
	free(executors[1]);

	return 0;
}

void rand_input1(float *model_input)
{
	*model_input =
		((INPUT1_MAX_VAL - INPUT1_MIN_VAL) * (float)sys_rand32_get() / (float)0xFFFFFFFF) +
		INPUT1_MIN_VAL;
}
