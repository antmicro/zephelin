/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

extern "C" {
#include <zpl.h>

#include <zephyr/kernel.h>
#include <zephyr/random/random.h>
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

using namespace tflm;

void rand_input0(float model_input[][INPUT0_SHAPE_1]);
void rand_input1(float *model_input);

int main(void)
{
	float __attribute((aligned(32))) model0_input[INPUT0_SHAPE_0][INPUT0_SHAPE_1];
	float model1_input;
	uint8_t model1_input_q;
	tflite::MicroInterpreter* interpreters[] = {nullptr, nullptr};
	int status = 0;

	zpl_init();

	#ifdef CONFIG_ZPL_TRACE_BACKEND_USB
	k_sleep(K_MSEC(500));
	#endif

	model_init();

	status = model_load(model0_data, interpreters[0], 15500);
	if (status) {
		printk("Model 0 load failed %d\n", status);
		return 1;
	}
	status = model_load(model1_data, interpreters[1]);
	if (status) {
		printk("Model 1 load failed %d\n", status);
		return 1;
	}

	for (short i = 0; i < N_SAMPLES; ++i) {

		rand_input0(model0_input);
		status = model_load_input(interpreters[0], (uint8_t *)model0_input,
				sizeof(float) * INPUT0_SHAPE_0 * INPUT0_SHAPE_1);
		if (status) {
			printk("Model 0 load input failed %d\n", status);
			break;
		}

		status = model_run(interpreters[0]);
		if (status) {
			printk("Model 0 run failed %d\n", status);
			break;
		}

		rand_input1(&model1_input);
		model1_input_q = (model1_input / INPUT1_SCALE) + INPUT1_ZERO;

		status = model_load_input(interpreters[1], (uint8_t *)&model1_input_q,
				sizeof(uint8_t));
		if (status) {
			printk("Model 1 load input failed %d\n", status);
			break;
		}

		status = model_run(interpreters[1]);
		if (status) {
			printk("Model 1 run failed %d\n", status);
			break;
		}
	}

	return 0;
}

void rand_input0(float model_input[][INPUT0_SHAPE_1])
{
	for (int i = 0; i < INPUT0_SHAPE_0; ++i) {
		for (int j = 0; j < INPUT0_SHAPE_1; ++j) {
			model_input[i][j] = (
					(INPUT0_MAX_VAL - INPUT0_MIN_VAL) *
					(float)sys_rand32_get() / (float)0xFFFFFFFF)
				+ INPUT0_MIN_VAL;
		}
	}
}

void rand_input1(float *model_input)
{
	*model_input =
		((INPUT1_MAX_VAL - INPUT1_MIN_VAL) * (float)sys_rand32_get() / (float)0xFFFFFFFF) +
		INPUT1_MIN_VAL;
}
