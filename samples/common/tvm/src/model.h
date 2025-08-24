/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef SAMPLES_TRACE_TVM_PROFILER_SRC_MODEL_H_
#define SAMPLES_TRACE_TVM_PROFILER_SRC_MODEL_H_

#include <stdint.h>

#define TVM_HEAP_SIZE 90

int model_init(void);
int model_load(const uint8_t *model_graph, uint32_t model_graph_size, const uint8_t *model_params, uint32_t model_params_size);
int model_load_input(const uint8_t *input, uint32_t input_size);
int model_run(void);
int model_get_output(uint8_t *output);

#endif /* SAMPLES_TRACE_TVM_PROFILER_SRC_MODEL_H_ */
