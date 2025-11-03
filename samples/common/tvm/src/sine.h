/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef SAMPLES_TRACE_TVM_PROFILER_SRC_SINE_H_
#define SAMPLES_TRACE_TVM_PROFILER_SRC_SINE_H_

#include <tvm/runtime/crt/module.h>
#include <tvm/runtime/crt/packed_func.h>

#define TVMGEN_QUANTIZED_FUNCTIONS(FUNC)                                                           \
	FUNC(tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast)               \
	FUNC(tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_1)             \
	FUNC(tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_2)             \
	FUNC(tvmgen_quantized_fused_reshape_cast_subtract)                                         \
	FUNC(tvmgen_quantized_fused_reshape_cast_subtract_1)

#define TVMGEN_QUANTIZED_FUNCTIONS_COUNT "\x05"

#define TVMGEN_QUANTIZED_DECLARE(func_name)                                                        \
	extern int32_t func_name(void *args, int32_t *arg_type_ids, int32_t num_args,              \
				 void *out_ret_value, int32_t *out_ret_tcode,                      \
				 void *resource_handle);

#define TVMGEN_QUANTIZED_FUNC_ARRAY(func_name) (TVMBackendPackedCFunc) func_name,

#define TVMGEN_QUANTIZED_FUNC_REGISTRY(func_name) "\0" #func_name

TVMGEN_QUANTIZED_FUNCTIONS(TVMGEN_QUANTIZED_DECLARE)

const TVMBackendPackedCFunc tvm_quantized_func_array[] = {
	TVMGEN_QUANTIZED_FUNCTIONS(TVMGEN_QUANTIZED_FUNC_ARRAY)};

const TVMFuncRegistry tvm_quantized_func_reg = {
	.names = TVMGEN_QUANTIZED_FUNCTIONS_COUNT TVMGEN_QUANTIZED_FUNCTIONS(
		TVMGEN_QUANTIZED_FUNC_REGISTRY) "\0",
	.funcs = tvm_quantized_func_array};

const TVMModule g_tvm_quantized_module = {&tvm_quantized_func_reg};

const TVMModule *TVMQuantizedLibEntryPoint(void)
{
	return &g_tvm_quantized_module;
}

#endif /* SAMPLES_TRACE_TVM_PROFILER_SRC_SINE_H_ */
