/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef SAMPLES_TRACE_TVM_PROFILER_SRC_MODEL_H_
#define SAMPLES_TRACE_TVM_PROFILER_SRC_MODEL_H_

#include <stdint.h>
#include <tvm/runtime/c_runtime_api.h>
#include <tvm/runtime/crt/graph_executor.h>

int model_init(void);
int model_load(const uint8_t *model_graph, uint32_t model_graph_size, const uint8_t *model_params, uint32_t model_params_size, TVMGraphExecutor **tvm_graph_executor, TVMModuleHandle *tvm_module_handle, const TVMModule *tvm_module);
int model_load_input(const uint8_t *input, uint32_t input_size, TVMGraphExecutor *tvm_graph_executor, bool quantized);
int model_run(TVMGraphExecutor *tvm_graph_executor);
int model_get_output(uint8_t *output, TVMGraphExecutor *tvm_graph_executor, bool quantized);

#endif /* SAMPLES_TRACE_TVM_PROFILER_SRC_MODEL_H_ */
