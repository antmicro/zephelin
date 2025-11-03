/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

/* tvm target: c -keys=cpu */
#define TVM_EXPORTS
#include "tvm/runtime/c_backend_api.h"
#include "tvm/runtime/c_runtime_api.h"
#include <math.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_1(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_2(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_quantized_fused_reshape_cast_subtract(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_quantized_fused_reshape_cast_subtract_1(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *p1 = (((TVMValue *)args)[1].v_handle);
	void *p2 = (((TVMValue *)args)[2].v_handle);
	void *p3 = (((TVMValue *)args)[3].v_handle);
	void *T_cast = (((TVMValue *)args)[4].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *p1_1 = (((DLTensor *)p1)[0].data);
	void *p2_1 = (((DLTensor *)p2)[0].data);
	void *p3_1 = (((DLTensor *)p3)[0].data);
	void *T_cast_1 = (((DLTensor *)T_cast)[0].data);
	int16_t packed_weight[16];

	for (int32_t z = 0; z < 2; ++z) {
		for (int32_t x = 0; x < 8; ++x) {
			int32_t cse_var_1 = ((z * 8) + x);
			packed_weight[cse_var_1] = ((int16_t *)p1_1)[cse_var_1];
		}
	}
	for (int32_t ax1_outer_ax0_outer_fused = 0; ax1_outer_ax0_outer_fused < 2;
	     ++ax1_outer_ax0_outer_fused) {
		int32_t compute_global[8];
		for (int32_t x_c_init = 0; x_c_init < 8; ++x_c_init) {
			compute_global[x_c_init] = 0;
		}
		for (int32_t x_c = 0; x_c < 8; ++x_c) {
			compute_global[x_c] = (compute_global[x_c] +
					       (((int32_t)((int16_t *)p0_1)[0]) *
						((int32_t)packed_weight[(
							(ax1_outer_ax0_outer_fused * 8) + x_c)])));
		}
		for (int32_t ax1_inner_inner = 0; ax1_inner_inner < 8; ++ax1_inner_inner) {
			int32_t cse_var_2 = ((ax1_outer_ax0_outer_fused * 8) + ax1_inner_inner);
			int32_t v_ =
				((int32_t *)p3_1)[0] +
				((int32_t)(((((0 != 0)
						      ? (((int64_t)(compute_global
									    [ax1_inner_inner] +
								    ((int32_t *)p2_1)[cse_var_2]))
							 << ((int64_t)0))
						      : ((int64_t)(compute_global[ax1_inner_inner] +
								   ((int32_t *)p2_1)[cse_var_2]))) *
					     (int64_t)1169592283) +
					    ((int64_t)1 << ((int64_t)((6 + 31) - 1)))) >>
					   ((int64_t)(6 + 31))));
			int32_t v__1 = (v_) < (127) ? (v_) : (127);
			((int8_t *)T_cast_1)[cse_var_2] =
				((int8_t)((v__1) > (-128) ? (v__1) : (-128)));
		}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_1(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *p1 = (((TVMValue *)args)[1].v_handle);
	void *p2 = (((TVMValue *)args)[2].v_handle);
	void *p3 = (((TVMValue *)args)[3].v_handle);
	void *T_cast = (((TVMValue *)args)[4].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *p1_1 = (((DLTensor *)p1)[0].data);
	void *p2_1 = (((DLTensor *)p2)[0].data);
	void *p3_1 = (((DLTensor *)p3)[0].data);
	void *T_cast_1 = (((DLTensor *)T_cast)[0].data);
	int16_t packed_weight[256];

	for (int32_t z = 0; z < 2; ++z) {
		for (int32_t y = 0; y < 16; ++y) {
			for (int32_t x = 0; x < 8; ++x) {
				int32_t cse_var_1 = (z * 128);
				packed_weight[((cse_var_1 + (y * 8)) + x)] =
					((int16_t *)p1_1)[((cse_var_1 + (x * 16)) + y)];
			}
		}
	}
	for (int32_t ax1_outer_ax0_outer_fused = 0; ax1_outer_ax0_outer_fused < 2;
	     ++ax1_outer_ax0_outer_fused) {
		int32_t compute_global[8];
		for (int32_t x_c_init = 0; x_c_init < 8; ++x_c_init) {
			compute_global[x_c_init] = 0;
		}
		for (int32_t k_outer = 0; k_outer < 16; ++k_outer) {
			for (int32_t x_c = 0; x_c < 8; ++x_c) {
				compute_global[x_c] = (compute_global[x_c] +
						       (((int32_t)((int16_t *)p0_1)[k_outer]) *
							((int32_t)packed_weight[(
								((ax1_outer_ax0_outer_fused * 128) +
								 (k_outer * 8)) +
								x_c)])));
			}
		}
		for (int32_t ax1_inner_inner = 0; ax1_inner_inner < 8; ++ax1_inner_inner) {
			int32_t cse_var_2 = ((ax1_outer_ax0_outer_fused * 8) + ax1_inner_inner);
			int32_t v_ =
				((int32_t *)p3_1)[0] +
				((int32_t)(((((0 != 0)
						      ? (((int64_t)(compute_global
									    [ax1_inner_inner] +
								    ((int32_t *)p2_1)[cse_var_2]))
							 << ((int64_t)0))
						      : ((int64_t)(compute_global[ax1_inner_inner] +
								   ((int32_t *)p2_1)[cse_var_2]))) *
					     (int64_t)1799926384) +
					    ((int64_t)1 << ((int64_t)((5 + 31) - 1)))) >>
					   ((int64_t)(5 + 31))));
			int32_t v__1 = (v_) < (127) ? (v_) : (127);
			((int8_t *)T_cast_1)[cse_var_2] =
				((int8_t)((v__1) > (-128) ? (v__1) : (-128)));
		}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_2(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *p1 = (((TVMValue *)args)[1].v_handle);
	void *p2 = (((TVMValue *)args)[2].v_handle);
	void *T_cast = (((TVMValue *)args)[3].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *p1_1 = (((DLTensor *)p1)[0].data);
	void *p2_1 = (((DLTensor *)p2)[0].data);
	void *T_cast_1 = (((DLTensor *)T_cast)[0].data);
	int16_t packed_weight[16];
	int32_t compute_global[1];

	for (int32_t y = 0; y < 16; ++y) {
		packed_weight[y] = ((int16_t *)p1_1)[y];
	}
	compute_global[0] = 0;
	for (int32_t k_outer = 0; k_outer < 16; ++k_outer) {
		compute_global[0] = (compute_global[0] + (((int32_t)((int16_t *)p0_1)[k_outer]) *
							  ((int32_t)packed_weight[k_outer])));
	}
	int32_t v_ =
		((int32_t)(((((0 != 0) ? (((int64_t)(compute_global[0] + ((int32_t *)p2_1)[0]))
					  << ((int64_t)0))
				       : ((int64_t)(compute_global[0] + ((int32_t *)p2_1)[0]))) *
			     (int64_t)1623168516) +
			    ((int64_t)1 << ((int64_t)((7 + 31) - 1)))) >>
			   ((int64_t)(7 + 31)))) +
		4;
	int32_t v__1 = (v_) < (127) ? (v_) : (127);
	((int8_t *)T_cast_1)[0] = ((int8_t)((v__1) > (-128) ? (v__1) : (-128)));
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_quantized_fused_reshape_cast_subtract(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *p1 = (((TVMValue *)args)[1].v_handle);
	void *T_subtract = (((TVMValue *)args)[2].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *p1_1 = (((DLTensor *)p1)[0].data);
	void *T_subtract_1 = (((DLTensor *)T_subtract)[0].data);

	((int16_t *)T_subtract_1)[0] = (((int16_t)((int8_t *)p0_1)[0]) - ((int16_t *)p1_1)[0]);
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_quantized_fused_reshape_cast_subtract_1(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *p1 = (((TVMValue *)args)[1].v_handle);
	void *T_subtract = (((TVMValue *)args)[2].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *p1_1 = (((DLTensor *)p1)[0].data);
	void *T_subtract_1 = (((DLTensor *)T_subtract)[0].data);

	for (int32_t ax1_inner = 0; ax1_inner < 16; ++ax1_inner) {
		((int16_t *)T_subtract_1)[ax1_inner] =
			(((int16_t)((int8_t *)p0_1)[ax1_inner]) - ((int16_t *)p1_1)[0]);
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_1(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_2(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_sine2_fused_reshape_cast_subtract(void *args, int32_t *arg_type_ids,
								 int32_t num_args,
								 void *out_ret_value,
								 int32_t *out_ret_tcode,
								 void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_sine2_fused_reshape_cast_subtract_1(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *p1 = (((TVMValue *)args)[1].v_handle);
	void *p2 = (((TVMValue *)args)[2].v_handle);
	void *p3 = (((TVMValue *)args)[3].v_handle);
	void *T_cast = (((TVMValue *)args)[4].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *p1_1 = (((DLTensor *)p1)[0].data);
	void *p2_1 = (((DLTensor *)p2)[0].data);
	void *p3_1 = (((DLTensor *)p3)[0].data);
	void *T_cast_1 = (((DLTensor *)T_cast)[0].data);
	int16_t packed_weight[16];

	for (int32_t z = 0; z < 2; ++z) {
		for (int32_t x = 0; x < 8; ++x) {
			int32_t cse_var_1 = ((z * 8) + x);
			packed_weight[cse_var_1] = ((int16_t *)p1_1)[cse_var_1];
		}
	}
	for (int32_t ax1_outer_ax0_outer_fused = 0; ax1_outer_ax0_outer_fused < 2;
	     ++ax1_outer_ax0_outer_fused) {
		int32_t compute_global[8];
		for (int32_t x_c_init = 0; x_c_init < 8; ++x_c_init) {
			compute_global[x_c_init] = 0;
		}
		for (int32_t x_c = 0; x_c < 8; ++x_c) {
			compute_global[x_c] = (compute_global[x_c] +
					       (((int32_t)((int16_t *)p0_1)[0]) *
						((int32_t)packed_weight[(
							(ax1_outer_ax0_outer_fused * 8) + x_c)])));
		}
		for (int32_t ax1_inner_inner = 0; ax1_inner_inner < 8; ++ax1_inner_inner) {
			int32_t cse_var_2 = ((ax1_outer_ax0_outer_fused * 8) + ax1_inner_inner);
			int32_t v_ =
				((int32_t *)p3_1)[0] +
				((int32_t)(((((0 != 0)
						      ? (((int64_t)(compute_global
									    [ax1_inner_inner] +
								    ((int32_t *)p2_1)[cse_var_2]))
							 << ((int64_t)0))
						      : ((int64_t)(compute_global[ax1_inner_inner] +
								   ((int32_t *)p2_1)[cse_var_2]))) *
					     (int64_t)1169592283) +
					    ((int64_t)1 << ((int64_t)((6 + 31) - 1)))) >>
					   ((int64_t)(6 + 31))));
			int32_t v__1 = (v_) < (127) ? (v_) : (127);
			((int8_t *)T_cast_1)[cse_var_2] =
				((int8_t)((v__1) > (-128) ? (v__1) : (-128)));
		}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_1(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *p1 = (((TVMValue *)args)[1].v_handle);
	void *p2 = (((TVMValue *)args)[2].v_handle);
	void *p3 = (((TVMValue *)args)[3].v_handle);
	void *T_cast = (((TVMValue *)args)[4].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *p1_1 = (((DLTensor *)p1)[0].data);
	void *p2_1 = (((DLTensor *)p2)[0].data);
	void *p3_1 = (((DLTensor *)p3)[0].data);
	void *T_cast_1 = (((DLTensor *)T_cast)[0].data);
	int16_t packed_weight[256];

	for (int32_t z = 0; z < 2; ++z) {
		for (int32_t y = 0; y < 16; ++y) {
			for (int32_t x = 0; x < 8; ++x) {
				int32_t cse_var_1 = (z * 128);
				packed_weight[((cse_var_1 + (y * 8)) + x)] =
					((int16_t *)p1_1)[((cse_var_1 + (x * 16)) + y)];
			}
		}
	}
	for (int32_t ax1_outer_ax0_outer_fused = 0; ax1_outer_ax0_outer_fused < 2;
	     ++ax1_outer_ax0_outer_fused) {
		int32_t compute_global[8];
		for (int32_t x_c_init = 0; x_c_init < 8; ++x_c_init) {
			compute_global[x_c_init] = 0;
		}
		for (int32_t k_outer = 0; k_outer < 16; ++k_outer) {
			for (int32_t x_c = 0; x_c < 8; ++x_c) {
				compute_global[x_c] = (compute_global[x_c] +
						       (((int32_t)((int16_t *)p0_1)[k_outer]) *
							((int32_t)packed_weight[(
								((ax1_outer_ax0_outer_fused * 128) +
								 (k_outer * 8)) +
								x_c)])));
			}
		}
		for (int32_t ax1_inner_inner = 0; ax1_inner_inner < 8; ++ax1_inner_inner) {
			int32_t cse_var_2 = ((ax1_outer_ax0_outer_fused * 8) + ax1_inner_inner);
			int32_t v_ =
				((int32_t *)p3_1)[0] +
				((int32_t)(((((0 != 0)
						      ? (((int64_t)(compute_global
									    [ax1_inner_inner] +
								    ((int32_t *)p2_1)[cse_var_2]))
							 << ((int64_t)0))
						      : ((int64_t)(compute_global[ax1_inner_inner] +
								   ((int32_t *)p2_1)[cse_var_2]))) *
					     (int64_t)1799926384) +
					    ((int64_t)1 << ((int64_t)((5 + 31) - 1)))) >>
					   ((int64_t)(5 + 31))));
			int32_t v__1 = (v_) < (127) ? (v_) : (127);
			((int8_t *)T_cast_1)[cse_var_2] =
				((int8_t)((v__1) > (-128) ? (v__1) : (-128)));
		}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_2(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *p1 = (((TVMValue *)args)[1].v_handle);
	void *p2 = (((TVMValue *)args)[2].v_handle);
	void *T_cast = (((TVMValue *)args)[3].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *p1_1 = (((DLTensor *)p1)[0].data);
	void *p2_1 = (((DLTensor *)p2)[0].data);
	void *T_cast_1 = (((DLTensor *)T_cast)[0].data);
	int16_t packed_weight[16];
	int32_t compute_global[1];

	for (int32_t y = 0; y < 16; ++y) {
		packed_weight[y] = ((int16_t *)p1_1)[y];
	}
	compute_global[0] = 0;
	for (int32_t k_outer = 0; k_outer < 16; ++k_outer) {
		compute_global[0] = (compute_global[0] + (((int32_t)((int16_t *)p0_1)[k_outer]) *
							  ((int32_t)packed_weight[k_outer])));
	}
	int32_t v_ =
		((int32_t)(((((0 != 0) ? (((int64_t)(compute_global[0] + ((int32_t *)p2_1)[0]))
					  << ((int64_t)0))
				       : ((int64_t)(compute_global[0] + ((int32_t *)p2_1)[0]))) *
			     (int64_t)1623168516) +
			    ((int64_t)1 << ((int64_t)((7 + 31) - 1)))) >>
			   ((int64_t)(7 + 31)))) +
		4;
	int32_t v__1 = (v_) < (127) ? (v_) : (127);
	((int8_t *)T_cast_1)[0] = ((int8_t)((v__1) > (-128) ? (v__1) : (-128)));
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_sine2_fused_reshape_cast_subtract(void *args, int32_t *arg_type_ids,
								 int32_t num_args,
								 void *out_ret_value,
								 int32_t *out_ret_tcode,
								 void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *p1 = (((TVMValue *)args)[1].v_handle);
	void *T_subtract = (((TVMValue *)args)[2].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *p1_1 = (((DLTensor *)p1)[0].data);
	void *T_subtract_1 = (((DLTensor *)T_subtract)[0].data);

	((int16_t *)T_subtract_1)[0] = (((int16_t)((int8_t *)p0_1)[0]) - ((int16_t *)p1_1)[0]);
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
	TVM_DLL int32_t tvmgen_sine2_fused_reshape_cast_subtract_1(
		void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
		int32_t *out_ret_tcode, void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *p1 = (((TVMValue *)args)[1].v_handle);
	void *T_subtract = (((TVMValue *)args)[2].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *p1_1 = (((DLTensor *)p1)[0].data);
	void *T_subtract_1 = (((DLTensor *)T_subtract)[0].data);

	for (int32_t ax1_inner = 0; ax1_inner < 16; ++ax1_inner) {
		((int16_t *)T_subtract_1)[ax1_inner] =
			(((int16_t)((int8_t *)p0_1)[ax1_inner]) - ((int16_t *)p1_1)[0]);
	}
	return 0;
}
