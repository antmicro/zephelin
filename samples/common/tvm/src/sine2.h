/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef SAMPLES_TRACE_TVM_PROFILER_SRC_SINE2_H_
#define SAMPLES_TRACE_TVM_PROFILER_SRC_SINE2_H_

#include <tvm/runtime/crt/module.h>
#include <tvm/runtime/crt/packed_func.h>

#define TVMGEN_SINE2_FUNCTIONS(FUNC)                                                               \
	FUNC(tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast)                   \
	FUNC(tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_1)                 \
	FUNC(tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_2)                 \
	FUNC(tvmgen_sine2_fused_reshape_cast_subtract)                                             \
	FUNC(tvmgen_sine2_fused_reshape_cast_subtract_1)

#define TVMGEN_SINE2_FUNCTIONS_COUNT "\x05"

#define TVMGEN_SINE2_DECLARE(func_name)                                                            \
	extern int32_t func_name(void *args, int32_t *arg_type_ids, int32_t num_args,              \
				 void *out_ret_value, int32_t *out_ret_tcode,                      \
				 void *resource_handle);

#define TVMGEN_SINE2_FUNC_ARRAY(func_name) (TVMBackendPackedCFunc) func_name,

#define TVMGEN_SINE2_FUNC_REGISTRY(func_name) "\0" #func_name

TVMGEN_SINE2_FUNCTIONS(TVMGEN_SINE2_DECLARE)

const TVMBackendPackedCFunc tvm_sine2_func_array[] = {
	TVMGEN_SINE2_FUNCTIONS(TVMGEN_SINE2_FUNC_ARRAY)};

const TVMFuncRegistry tvm_sine2_func_reg = {
	.names = TVMGEN_SINE2_FUNCTIONS_COUNT TVMGEN_SINE2_FUNCTIONS(
		TVMGEN_SINE2_FUNC_REGISTRY) "\0",
	.funcs = tvm_sine2_func_array};

const TVMModule g_tvm_sine2_module = {&tvm_sine2_func_reg};

const TVMModule *TVMSine2LibEntryPoint(void)
{
	return &g_tvm_sine2_module;
}

#endif /* SAMPLES_TRACE_TVM_PROFILER_SRC_SINE2_H_ */
