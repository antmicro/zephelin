/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl.h>

#include <math.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/kernel.h>
#include <zephyr/random/random.h>
#include <generated/model_data_graph.h>
#include <generated/model_data_params.h>
#include <model.h>

#define INPUT_SHAPE_0 128
#define INPUT_SHAPE_1 3

#define OUTPUT_SHAPE_0 1
#define OUTPUT_SHAPE_1 4

#define MOVEMENT_THRESHOLD 0.01f

K_SEM_DEFINE(run_inference, 0, 1);
K_MUTEX_DEFINE(data_buffer_mutex);
int sample_idx;
static float data_buffer[INPUT_SHAPE_0][INPUT_SHAPE_1];
const struct device *const accelerometer = DEVICE_DT_GET(DT_ALIAS(accel));

/**
 * Magic Wand dataset classes
 */
const char *class_names[OUTPUT_SHAPE_1] = {"wing", "ring", "slope", "negative"};

void read_input(float *model_input);

void read_accel_data(float *x, float *y, float *z);

void read_accel_data_fun(void);

int main(void)
{
	int status = 0;
	float __attribute((aligned(32))) model_input[INPUT_SHAPE_0][INPUT_SHAPE_1];
	float __attribute((aligned(32))) model_output[OUTPUT_SHAPE_0][OUTPUT_SHAPE_1];

	zpl_init();

	status = model_init();
	if (status) {
		printk("Model init failed %d\n", status);
		return 1;
	}

	status = model_load(model_data_graph, model_data_graph_len, model_data_params,
			    model_data_params_len);
	if (status) {
		printk("Model load failed %d\n", status);
		return 1;
	}

	for (;;) {
		if (k_sem_take(&run_inference, K_NO_WAIT) != 0) {
			k_msleep(10);
			continue;
		}

		read_input((float *)model_input);

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

		status = model_get_output((uint8_t *)model_output);
		if (status) {
			printk("Model get output failed %d\n", status);
			break;
		}
		printk("model output: ");
		for (int i = 0; i < OUTPUT_SHAPE_1; ++i) {
			int value_int = (int)(1000 * model_output[0][i]);
			printk("%s=%d.%03d ", class_names[i], value_int / 1000, value_int % 1000);
		}
		printk("\n");
	}

	return 0;
}

void read_input(float *model_input)
{
	if (k_mutex_lock(&data_buffer_mutex, K_FOREVER) == 0) {
		memcpy(model_input, &data_buffer[sample_idx][0],
		       (INPUT_SHAPE_0 - sample_idx) * sizeof(float) * INPUT_SHAPE_1);
		if (sample_idx > 0) {
			memcpy(&model_input[(INPUT_SHAPE_0 - sample_idx) * INPUT_SHAPE_1],
			       data_buffer, sample_idx * sizeof(float) * INPUT_SHAPE_1);
		}

		k_mutex_unlock(&data_buffer_mutex);
	}
}

void read_accel_data(float *x, float *y, float *z)
{
	struct sensor_value val[3];
	int32_t ret = 0;

	*x = 0.0f;
	*y = 0.0f;
	*z = 0.0f;

	do {
		if (!device_is_ready(accelerometer)) {
			printk("%s: not ready\n", accelerometer->name);
			break;
		}

		ret = sensor_sample_fetch(accelerometer);
		if (ret < 0 && ret != -EBADMSG) {
			printk("%s: failed to fetch sample\n", accelerometer->name);
			break;
		}

		ret = sensor_channel_get(accelerometer, SENSOR_CHAN_ACCEL_XYZ, val);
		if (ret < 0) {
			printk("%s: failed to read channel\n", accelerometer->name);
			break;
		}

		*x = sensor_value_to_float(&val[0]) / (2 * 9.807);
		*y = sensor_value_to_float(&val[1]) / (2 * 9.807);
		*z = sensor_value_to_float(&val[2]) / (2 * 9.807);

		printk("%s: ", accelerometer->name);
		printk(
			"x=%c%d.%03d ",
			(*x > 0 ? '+' : '-'),
			abs((int)(*x)),
			abs((int)((*x) * 1000)) % 1000
		);
		printk(
			"y=%c%d.%03d ",
			(*y > 0 ? '+' : '-'),
			abs((int)(*y)),
			abs((int)((*y) * 1000)) % 1000
		);
		printk(
			"z=%c%d.%03d\n",
			(*z > 0 ? '+' : '-'),
			abs((int)(*z)),
			abs((int)((*z) * 1000)) % 1000
		);
	} while (0);
}

void read_accel_data_fun(void)
{
	float prev_x = 0.0f, prev_y = 0.0f, prev_z = 0.0f;
	float x, y, z;

	while (true) {
		read_accel_data(&x, &y, &z);

		if (k_mutex_lock(&data_buffer_mutex, K_FOREVER) == 0) {
			/* convert to mili G */
			data_buffer[sample_idx][0] = 1000.0f * x;
			data_buffer[sample_idx][1] = 1000.0f * y;
			data_buffer[sample_idx][2] = 1000.0f * z;

			k_mutex_unlock(&data_buffer_mutex);

			++sample_idx;
			sample_idx %= INPUT_SHAPE_0;
		}

		/* run inference every 16 samples if accelerometer is moving */
		if ((fabsf(prev_x - x) + fabsf(prev_y - y) + fabsf(prev_z - z) >
		     MOVEMENT_THRESHOLD) &&
		    (sample_idx % 16) == 0) {
			k_sem_give(&run_inference);
		}

		prev_x = x;
		prev_y = y;
		prev_z = z;

		k_msleep(10);
	}
}

K_THREAD_DEFINE(read_accel_data_thread, 512, read_accel_data_fun, NULL, NULL, NULL, -1, 0, 100);
