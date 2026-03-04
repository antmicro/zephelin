/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl.h>

#include "tvm/runtime/c_runtime_api.h"
#include "tvm/runtime/crt/graph_executor.h"
#include "tvm/runtime/crt/internal/graph_executor/graph_executor.h"

#include <generated/model_data_graph.h>
#include <generated/model_data_params.h>
#include <generated/model_data_int8_graph.h>
#include <generated/model_data_int8_params.h>
#include <zephyr/kernel.h>
#include <zephyr/random/random.h>

#include <tvm_model.h>
#include <sine.h>

/* available models */
enum ModelType {
	MAGIC_WAND = 0,
	SINE = 1,
};

/* models to use */
const enum ModelType model_types[] = {MAGIC_WAND, SINE, MAGIC_WAND};

/* number of threads to run */
#define THREADS_NUM ARRAY_SIZE(model_types)

/* size of stack area used by each thread */
#define STACK_SIZE 2048

static K_THREAD_STACK_ARRAY_DEFINE(tstack, THREADS_NUM, STACK_SIZE);
static struct k_thread tthread[THREADS_NUM];
static struct k_sem tsem_start[THREADS_NUM];
static struct k_sem tsem_done[THREADS_NUM];

/* Magic Wand input spec */
#define INPUT0_SHAPE_0 128
#define INPUT0_SHAPE_1 3
#define INPUT0_MIN_VAL -2040.0f
#define INPUT0_MAX_VAL 2040.0f
#define INPUT0_SIZE    (sizeof(float) * INPUT0_SHAPE_0 * INPUT0_SHAPE_1)

/* Sine input spec */
#define INPUT1_MIN_VAL 0.0f
#define INPUT1_MAX_VAL (2.0f * 3.14159265359f)
#define INPUT1_SCALE   0.024573976173996925f
#define INPUT1_ZERO    -128
#define INPUT1_SIZE    (sizeof(uint8_t))

struct ModelData {
	TVMGraphExecutor *executor;
	TVMModuleHandle module_handle;
	uint8_t *input;
	size_t input_size;
	struct k_sem *sem_start;
	struct k_sem *sem_done;
	bool quantized;
};

void rand_input0(uint8_t *model_input);
void rand_input1(uint8_t *model_input);

void thread_run_model(void *model_data_, void *arg2, void *arg3)
{
	struct ModelData *model_data = (struct ModelData *)model_data_;

	char thread_name[20];
	int status = 0;

	snprintf(thread_name, sizeof(thread_name), "%s", k_thread_name_get(k_current_get()));

	while (true) {
		k_sem_take(model_data->sem_start, K_FOREVER);

		printk("\t%s: running on cpu %d\n", thread_name, arch_curr_cpu()->id);

		status = model_load_input(model_data->input, model_data->input_size,
					  model_data->executor, model_data->quantized);
		if (status) {
			printk("\t%s: model load input failed %d\n", thread_name, status);
			break;
		}

		status = model_run(model_data->executor);
		if (status) {
			printk("\t%s: model run failed %d\n", thread_name, status);
			break;
		}

		printk("\t%s: done on cpu %d\n", thread_name, arch_curr_cpu()->id);

		k_sem_give(model_data->sem_done);
	}
}

int main(void)
{
	struct ModelData model_data[THREADS_NUM];
	int status = 0;

#ifdef CONFIG_ZPL_TRACE_BACKEND_USB
	k_sleep(K_MSEC(500));
#endif

	model_init();

	/* alloc models inputs */
	for (int i = 0; i < THREADS_NUM; ++i) {
		switch (model_types[i]) {
		case MAGIC_WAND:
			model_data[i].input = (uint8_t *)(k_aligned_alloc(32, INPUT0_SIZE));
			model_data[i].input_size = INPUT0_SIZE;
			break;
		case SINE:
			model_data[i].input = (uint8_t *)(k_aligned_alloc(32, INPUT1_SIZE));
			model_data[i].input_size = INPUT1_SIZE;
			break;
		default:
			printk("Unknown model type %d\n", i);
			return 1;
		}
	}

	/* load models */
	for (int i = 0; i < THREADS_NUM; ++i) {
		model_data[i].executor =
			(TVMGraphExecutor *)k_aligned_alloc(32, sizeof(TVMGraphExecutor));
		model_data[i].module_handle = NULL;
		switch (model_types[i]) {
		case MAGIC_WAND:
			status = model_load(model_data_graph, model_data_graph_len,
					    model_data_params, model_data_params_len,
					    &model_data[i].executor, &model_data[i].module_handle,
					    NULL);
			model_data[i].quantized = false;
			break;
		case SINE:
			status = model_load(model_data_int8_graph, model_data_int8_graph_len,
					    model_data_int8_params, model_data_int8_params_len,
					    &model_data[i].executor, &model_data[i].module_handle,
					    TVMQuantizedLibEntryPoint());
			model_data[i].quantized = true;
			break;
		}
		if (status) {
			printk("Model %d load failed %d\n", i, status);
			return 1;
		}
	}

	/* create and start threads */
	for (int i = 0; i < THREADS_NUM; ++i) {
		k_sem_init(&tsem_start[i], 0, 1);
		k_sem_init(&tsem_done[i], 1, 1);
		model_data[i].sem_start = &tsem_start[i];
		model_data[i].sem_done = &tsem_done[i];

		k_thread_create(&tthread[i], tstack[i], STACK_SIZE, thread_run_model,
				(void *)&model_data[i], NULL, NULL, 9, 0, K_FOREVER);
		char thread_name[32];
		switch (model_types[i]) {
		case MAGIC_WAND:
			snprintf(thread_name, sizeof(thread_name), "magic_wand_%d", i);
			break;
		case SINE:
			snprintf(thread_name, sizeof(thread_name), "sine_%d", i);
			break;
		}
		k_thread_name_set(&tthread[i], thread_name);
		k_thread_cpu_pin(&tthread[i], i % (arch_num_cpus() - 1) + 1);
		k_thread_start(&tthread[i]);
		printk("Thread %d started\n", i);
	}

	while (true) {
		for (int i = 0; i < THREADS_NUM; ++i) {
			if (0 != k_sem_take(&tsem_done[i], K_NO_WAIT)) {
				continue;
			}

			switch (model_types[i]) {
			case MAGIC_WAND:
				rand_input0(model_data[i].input);
				break;
			case SINE:
				rand_input1(model_data[i].input);
				break;
			}
			k_sem_give(&tsem_start[i]);
			printk("Requested processing for thread %d\n", i);

			k_msleep(50);
		}
	}

	return 0;
}

void rand_input0(uint8_t *model_input)
{
	float *model_input_f = (float *)model_input;

	for (int i = 0; i < INPUT0_SHAPE_0; ++i) {
		for (int j = 0; j < INPUT0_SHAPE_1; ++j) {
			model_input_f[i * INPUT0_SHAPE_1 + j] =
				((INPUT0_MAX_VAL - INPUT0_MIN_VAL) * (float)sys_rand32_get() /
				 (float)0xFFFFFFFF) +
				INPUT0_MIN_VAL;
		}
	}
}

void rand_input1(uint8_t *model_input)
{
	float model_input_f =
		((INPUT1_MAX_VAL - INPUT1_MIN_VAL) * (float)sys_rand32_get() / (float)0xFFFFFFFF) +
		INPUT1_MIN_VAL;
	*model_input = (model_input_f / INPUT1_SCALE) + INPUT1_ZERO;
}
