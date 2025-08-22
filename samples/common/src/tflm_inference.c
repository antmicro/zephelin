/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl.h>

#include <zephyr/kernel.h>
#include <zephyr/random/random.h>
#include <generated/model_data.h>
#include <model.h>

#define N_SAMPLES 2
#define INPUT_SHAPE_0 128
#define INPUT_SHAPE_1 3
#define INPUT_MIN_VAL -2040.0f
#define INPUT_MAX_VAL 2040.0f

void rand_input(float model_input[][INPUT_SHAPE_1]);

int main(void)
{
	float __attribute((aligned(32))) model_input[INPUT_SHAPE_0][INPUT_SHAPE_1];
	int status = 0;

	zpl_init();

	#ifdef CONFIG_ZPL_TRACE_BACKEND_USB
	k_sleep(K_MSEC(500));
	#endif

	model_init();
	status = model_load(model_data, model_data_len);
	if (status) {
		printk("Model load failed %d\n", status);
		return 1;
	}

	for (int batch_index = 0; batch_index < N_SAMPLES; ++batch_index) {
		rand_input(model_input);
		status = model_load_input((uint8_t *)model_input,
				sizeof(float) * INPUT_SHAPE_0 * INPUT_SHAPE_1);
		if (status) {
			printk("Model load input failed %d\n", status);
			break;
		}

		status = model_run();
		if (status) {
			printk("Model run failed %d\n", status);
			break;
		}
	}

	return 0;
}

void rand_input(float model_input[][INPUT_SHAPE_1])
{
	for (int i = 0; i < INPUT_SHAPE_0; ++i) {
		for (int j = 0; j < INPUT_SHAPE_1; ++j) {
			model_input[i][j] = (
					(INPUT_MAX_VAL - INPUT_MIN_VAL) *
					(float)sys_rand32_get() / (float)0xFFFFFFFF)
				+ INPUT_MIN_VAL;
		}
	}
}
