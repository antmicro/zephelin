/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

extern "C" {
#include <zephyr/kernel.h>
#include <zephyr/random/random.h>
#include <zpl.h>
#include <zpl/configuration.h>
#include <generated/model0_data.h>
}
#include <tflm_model.h>

#define N_SAMPLES     10
#define INPUT_MIN_VAL 0.0f
#define INPUT_MAX_VAL (2.0f * 3.14159265359f)

#define INPUT_SCALE 0.024573976173996925f
#define INPUT_ZERO  -128

#define OUTPUT_SCALE 0.008472034707665443f
#define OUTPUT_ZERO  4

using namespace tflm;

ZPL_CODE_SCOPE_DEFINE(prepare_model, true);

void loop();

void rand_input(float *model_input);

int main(void)
{
	int status = 0;

	ZPL_MARK_CODE_SCOPE(prepare_model) {
		model_init();
		status = model_load(model0_data);
	}
	if (status) {
		printk("Model load failed %d\n", status);
		return 1;
	}

	unsigned int lock_key;
	for (int batch_index = 0; batch_index < N_SAMPLES; ++batch_index) {
		/* Lock IRQ to make sure sys_clock_isr will not be present in the trace */
		lock_key = irq_lock();
		loop();
		irq_unlock(lock_key);
	}

	return 0;
}

void loop()
{
	int status = 0;
	float model_input;
	uint8_t model_input_q;
	float model_output;
	uint8_t model_output_q;

	rand_input(&model_input);
	model_input_q = (model_input / INPUT_SCALE) + INPUT_ZERO;

	status = model_load_input((uint8_t *)&model_input_q, sizeof(uint8_t));
	if (status) {
		printk("Model load input failed %d\n", status);
		return;
	}

	status = model_run();
	if (status) {
		printk("Model run failed %d\n", status);
		return;
	}

	status = model_get_output((uint8_t *)&model_output_q, sizeof(uint8_t));
	if (status) {
		printk("Model get output failed %d\n", status);
		return;
	}
	model_output = (model_output_q - OUTPUT_ZERO) * OUTPUT_SCALE;

	printk("x_value: %f, y_value: %f\n", (double)model_input, (double)model_output);
}

void rand_input(float *model_input)
{
	*model_input =
		((INPUT_MAX_VAL - INPUT_MIN_VAL) * (float)sys_rand32_get() / (float)0xFFFFFFFF) +
		INPUT_MIN_VAL;
}
