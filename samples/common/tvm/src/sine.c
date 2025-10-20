/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


/* tvm target: c -keys=arm_cpu,cpu -device=arm_cpu -march=armv7e-m -mcpu=cortex-m4 -model=max32690 */
#define TVM_EXPORTS
#include "tvm/runtime/c_runtime_api.h"
#include "tvm/runtime/c_backend_api.h"
#include <math.h>
#include <stdbool.h>


#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <arm_acle.h>

#include <tvm/runtime/crt/error_codes.h>


#ifndef ARM_CPU_INTRINSICS_EXIST
#define ARM_CPU_INTRINSICS_EXIST
__inline__ __attribute__((always_inline)) uint32_t __ror(uint32_t op1, uint32_t op2)
{
	op2 %= 32U;
	if (op2 == 0U) {
		return op1;
	}
	return (op1 >> op2) | (op1 << (32U - op2));
}

#define __pkhbt(ARG1, ARG2, ARG3) __extension__ ({                            uint32_t __RES, __ARG1 = (ARG1), __ARG2 = (ARG2);   __asm("pkhbt %0, %1, %2, lsl %3" : "=r" (__RES) :  "r" (__ARG1), "r" (__ARG2), "I" (ARG3));   __RES;  })

#define __pkhtb(ARG1, ARG2, ARG3) __extension__ ({                            uint32_t __RES, __ARG1 = (ARG1), __ARG2 = (ARG2);   if (ARG3 == 0)     __asm("pkhtb %0, %1, %2" : "=r" (__RES) :  "r" (__ARG1), "r" (__ARG2));   else     __asm("pkhtb %0, %1, %2, asr %3" : "=r" (__RES) :  "r" (__ARG1), "r" (__ARG2), "I" (ARG3));   __RES;  })
#endif

#ifndef ARM_CPU_MPROFILE_READ_AND_PAD_EXISTS
#define ARM_CPU_MPROFILE_READ_AND_PAD_EXISTS
__attribute__((always_inline)) static inline const int8_t *read_and_pad(const int8_t *source, int32_t *out1, int32_t *out2)
{
	int32_t inA;

	  memcpy(&inA, source, 4);
	  source += 4;

	int32_t inAbuf1 = __sxtb16(__ror((uint32_t)inA, 8));
	int32_t inAbuf2 = __sxtb16(inA);
	  *out2 = (int32_t)(__pkhtb(inAbuf1, inAbuf2, 16));
	  *out1 = (int32_t)(__pkhbt(inAbuf2, inAbuf1, 16));

	return source;
}
#endif



#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1_body_rest_QYKAYUUR(
	  int32_t K_arg,
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int K = K_arg;
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int k_base = (K / 4) * 4;

	switch (K % 4) {
	case 1:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] = (int32_t) a_ptr[0] * (int32_t) b_ptr[0];
	}
	}
	break;
	case 2:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] =   (int32_t) a_ptr[0] * (int32_t) b_ptr[0]
				     + (int32_t) a_ptr[1] * (int32_t) b_ptr[1];
	}
	}
	break;
	case 3:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] =   (int32_t) a_ptr[0] * (int32_t) b_ptr[0]
				     + (int32_t) a_ptr[1] * (int32_t) b_ptr[1]
				     + (int32_t) a_ptr[2] * (int32_t) b_ptr[2];
	}
	}
	break;
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_body_loop_QYKAYUUR(
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;


	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int32_t sum = 0;

	for (int l = 0; l < 1; l++) {
	      sum += (int32_t) aa[i*A_stride + l] * (int32_t) bb[j*B_stride + l];
	}
	    /* NOTE: this is the line where `*_body` differs from `*_update`. here */
	    /* we're *setting* the result, instead of accumulating, because we know */
	    /* the `i` and `j` itervars span their entire respective axes. */
	    cc[i*C_stride + j] = sum;
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_body_QYKAYUUR(
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int16_t bb_pad[1];
	int32_t retcode = 0;

	if (1 < 2 && 1 < 2) {
	  retcode = gemm_1x1x1_body_loop_QYKAYUUR(aa, bb, cc, A_stride, B_stride, C_stride);
	goto out;
	}

	for (int i = 0; i < 1; i++)
	for (int j = 0; j < 1 / 4; j++)
	    read_and_pad(&bb[i*B_stride + j*4], (int32_t *) &bb_pad[i*1 + j*4], (int32_t *) &bb_pad[i*1 + j*4 + 2]);

	for (int i = 0; i < 1; i++) {
	  int16_t aa_pad_line[1];

	for (int l = 0; l < 1 / 4; l++)
	    read_and_pad(&aa[i*A_stride + l*4], (int32_t *) &aa_pad_line[l*4], (int32_t *) &aa_pad_line[l*4 + 2]);

	for (int j = 0; j < 1; j++) {
	int32_t *aa_ptr = (int32_t *) aa_pad_line;
	int32_t *bb_ptr = (int32_t *) &bb_pad[j*1];
	int32_t sum = 0;

	for (int l = 0; l < 2 * (1 / 4); l++) {
	      sum = __smlad(*aa_ptr, *bb_ptr, sum);
	      ++aa_ptr; ++bb_ptr;
	}
	    /* NOTE: this is the line where `*_body` differs from `*_update`. here */
	    /* we're *setting* the result, instead of accumulating, because we know */
	    /* the `i` and `j` itervars span their entire respective axes. */
	    cc[i*C_stride + j] = sum;
	}
	}

	if (1 % 4 != 0)
	  gemm_1x1_body_rest_QYKAYUUR(1, aa, bb, cc, A_stride, B_stride, C_stride);

out:
	return retcode;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1_update_rest_QYKAYUUR(
	  int32_t K_arg,
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int K = K_arg;
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int k_base = (K / 4) * 4;

	switch (K % 4) {
	case 1:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] += (int32_t) a_ptr[0] * (int32_t) b_ptr[0];
	}
	}
	break;
	case 2:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] +=   (int32_t) a_ptr[0] * (int32_t) b_ptr[0]
				      + (int32_t) a_ptr[1] * (int32_t) b_ptr[1];
	}
	}
	break;
	case 3:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] +=   (int32_t) a_ptr[0] * (int32_t) b_ptr[0]
				      + (int32_t) a_ptr[1] * (int32_t) b_ptr[1]
				      + (int32_t) a_ptr[2] * (int32_t) b_ptr[2];
	}
	}
	break;
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_update_loop_QYKAYUUR(
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int32_t sum = 0;

	for (int l = 0; l < 1; l++) {
	      sum += (int32_t) aa[i*A_stride + l] * (int32_t) bb[j*B_stride + l];
	}
	    cc[i*C_stride + j] += sum;
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_update_QYKAYUUR(
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int16_t bb_pad[1];
	int32_t retcode = 0;

	if (1 < 2 && 1 < 2) {
	  retcode = gemm_1x1x1_update_loop_QYKAYUUR(aa, bb, cc, A_stride, B_stride, C_stride);
	goto out;
	}

	for (int i = 0; i < 1; i++)
	for (int j = 0; j < 1 / 4; j++)
	    read_and_pad(&bb[i*B_stride + j*4], (int32_t *) &bb_pad[i*1 + j*4], (int32_t *) &bb_pad[i*1 + j*4 + 2]);

	for (int i = 0; i < 1; i++) {
	  int16_t aa_pad_line[1];

	for (int l = 0; l < 1 / 4; l++)
	    read_and_pad(&aa[i*A_stride + l*4], (int32_t *) &aa_pad_line[l*4], (int32_t *) &aa_pad_line[l*4 + 2]);

	for (int j = 0; j < 1; j++) {
	int32_t *aa_ptr = (int32_t *) aa_pad_line;
	int32_t *bb_ptr = (int32_t *) &bb_pad[j*1];
	int32_t sum = 0;

	for (int l = 0; l < 2 * (1 / 4); l++) {
	      sum = __smlad(*aa_ptr, *bb_ptr, sum);
	      ++aa_ptr; ++bb_ptr;
	}
	    cc[i*C_stride + j] += sum;
	}
	}

	if (1 % 4 != 0)
	  gemm_1x1_update_rest_QYKAYUUR(1, aa, bb, cc, A_stride, B_stride, C_stride);

out:
	return retcode;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1_body_rest_QYKAYUUR(
	  int32_t K_arg,
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int K = K_arg;
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int k_base = (K / 2) * 2;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int16_t *a_ptr = &aa[i * A_stride + k_base];
	int16_t *b_ptr = &bb[j * B_stride + k_base];

	    cc[i * C_stride + j] = (int32_t) a_ptr[0] * (int32_t) b_ptr[0];
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1x1_body_loop_QYKAYUUR(
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int32_t sum = 0;

	for (int l = 0; l < 1; l++) {
	      sum += (int32_t) aa[i*A_stride + l] * (int32_t) bb[j*B_stride + l];
	}
	    /* NOTE: this is the line where `*_body` differs from `*_update`. here */
	    /* we're *setting* the result, instead of accumulating, because we know */
	    /* the `i` and `j` itervars span their entire respective axes. */
	    cc[i*C_stride + j] = sum;
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1x1_body_QYKAYUUR(
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int32_t retcode = 0;

	if (1 < 2 && 1 < 2) {
	  retcode = gemm16_1x1x1_body_loop_QYKAYUUR(aa, bb, cc, A_stride, B_stride, C_stride);
	goto out;
	}

	if (((uint32_t)aa & 0x3) != 0 || ((uint32_t)bb & 0x3) != 0) {
	  retcode = kTvmErrorFunctionCallInvalidArg;
	goto out;
	}

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	    int32_t aa_vector[1 / 2];
	    int32_t bb_vector[1 / 2];

	    memcpy(&aa_vector, &aa[i * A_stride], sizeof(aa_vector));
	    memcpy(&bb_vector, &bb[j * B_stride], sizeof(bb_vector));

	int32_t sum = 0;

	for (int l = 0; l < 1 / 2; l++) {
	      sum = __smlad(aa_vector[l], bb_vector[l], sum);
	}
	    /* NOTE: this is the line where `*_body` differs from `*_update`. here */
	    /* we're *setting* the result, instead of accumulating, because we know */
	    /* the `i` and `j` itervars span their entire respective axes. */
	    cc[i*C_stride + j] = sum;
	}
	}

	if (1 % 2 != 0)
	  gemm16_1x1_body_rest_QYKAYUUR(1, aa, bb, cc, A_stride, B_stride, C_stride);

out:
	return retcode;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1_update_rest_QYKAYUUR(
	  int32_t K_arg,
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int K = K_arg;
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int k_base = (K / 2) * 2;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int16_t *a_ptr = &aa[i * A_stride + k_base];
	int16_t *b_ptr = &bb[j * B_stride + k_base];

	    cc[i * C_stride + j] += (int32_t) a_ptr[0] * (int32_t) b_ptr[0];
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1x1_update_loop_QYKAYUUR(
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int32_t sum = 0;

	for (int l = 0; l < 1; l++) {
	      sum += (int32_t) aa[i*A_stride + l] * (int32_t) bb[j*B_stride + l];
	}
	    cc[i*C_stride + j] += sum;
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1x1_update_QYKAYUUR(
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int32_t retcode = 0;

	if (1 < 2 && 1 < 2) {
	  retcode = gemm16_1x1x1_update_loop_QYKAYUUR(aa, bb, cc, A_stride, B_stride, C_stride);
	goto out;
	}

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	    int32_t aa_vector[1 / 2];
	    int32_t bb_vector[1 / 2];

	    memcpy(&aa_vector, &aa[i * A_stride], sizeof(aa_vector));
	    memcpy(&bb_vector, &bb[j * B_stride], sizeof(bb_vector));

	int32_t sum = 0;

	for (int l = 0; l < 1 / 2; l++) {
	      sum = __smlad(aa_vector[l], bb_vector[l], sum);
	}
	    cc[i*C_stride + j] += sum;
	}
	}

	if (1 % 2 != 0)
	  gemm16_1x1_update_rest_QYKAYUUR(1, aa, bb, cc, A_stride, B_stride, C_stride);

out:
	return retcode;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_reset_QYKAYUUR(int32_t *cc, int32_t C_stride)
{
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	    cc[i*C_stride + j] = 0;
	}
	}
	return 0;
}



#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <arm_acle.h>

#include <tvm/runtime/crt/error_codes.h>


#ifndef ARM_CPU_INTRINSICS_EXIST
#define ARM_CPU_INTRINSICS_EXIST
__attribute__((always_inline)) uint32_t __ror(uint32_t op1, uint32_t op2)
{
	op2 %= 32U;
	if (op2 == 0U) {
	return op1;
	}
	return (op1 >> op2) | (op1 << (32U - op2));
}

#define __pkhbt(ARG1, ARG2, ARG3) __extension__ ({                            uint32_t __RES, __ARG1 = (ARG1), __ARG2 = (ARG2);   __asm("pkhbt %0, %1, %2, lsl %3" : "=r" (__RES) :  "r" (__ARG1), "r" (__ARG2), "I" (ARG3));   __RES;  })

#define __pkhtb(ARG1, ARG2, ARG3) __extension__ ({                            uint32_t __RES, __ARG1 = (ARG1), __ARG2 = (ARG2);   if (ARG3 == 0)     __asm("pkhtb %0, %1, %2" : "=r" (__RES) :  "r" (__ARG1), "r" (__ARG2));   else     __asm("pkhtb %0, %1, %2, asr %3" : "=r" (__RES) :  "r" (__ARG1), "r" (__ARG2), "I" (ARG3));   __RES;  })
#endif

#ifndef ARM_CPU_MPROFILE_READ_AND_PAD_EXISTS
#define ARM_CPU_MPROFILE_READ_AND_PAD_EXISTS
__attribute__((always_inline)) static inline const int8_t *read_and_pad(const int8_t *source, int32_t *out1, int32_t *out2)
{
	int32_t inA;

	  memcpy(&inA, source, 4);
	  source += 4;

	int32_t inAbuf1 = __sxtb16(__ror((uint32_t)inA, 8));
	int32_t inAbuf2 = __sxtb16(inA);
	  *out2 = (int32_t)(__pkhtb(inAbuf1, inAbuf2, 16));
	  *out1 = (int32_t)(__pkhbt(inAbuf2, inAbuf1, 16));

	return source;
}
#endif



#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1_body_rest_BFAJQBRS(
	  int32_t K_arg,
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int K = K_arg;
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int k_base = (K / 4) * 4;

	switch (K % 4) {
	case 1:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] = (int32_t) a_ptr[0] * (int32_t) b_ptr[0];
	}
	}
	break;
	case 2:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] =   (int32_t) a_ptr[0] * (int32_t) b_ptr[0]
				     + (int32_t) a_ptr[1] * (int32_t) b_ptr[1];
	}
	}
	break;
	case 3:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] =   (int32_t) a_ptr[0] * (int32_t) b_ptr[0]
				     + (int32_t) a_ptr[1] * (int32_t) b_ptr[1]
				     + (int32_t) a_ptr[2] * (int32_t) b_ptr[2];
	}
	}
	break;
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_body_loop_BFAJQBRS(
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;


	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int32_t sum = 0;

	for (int l = 0; l < 1; l++) {
	      sum += (int32_t) aa[i*A_stride + l] * (int32_t) bb[j*B_stride + l];
	}
	    /* NOTE: this is the line where `*_body` differs from `*_update`. here */
	    /* we're *setting* the result, instead of accumulating, because we know */
	    /* the `i` and `j` itervars span their entire respective axes. */
	    cc[i*C_stride + j] = sum;
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_body_BFAJQBRS(
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int16_t bb_pad[1];
	int32_t retcode = 0;

	if (1 < 2 && 1 < 2) {
	  retcode = gemm_1x1x1_body_loop_BFAJQBRS(aa, bb, cc, A_stride, B_stride, C_stride);
	goto out;
	}

	for (int i = 0; i < 1; i++)
	for (int j = 0; j < 1 / 4; j++)
	    read_and_pad(&bb[i*B_stride + j*4], (int32_t *) &bb_pad[i*1 + j*4], (int32_t *) &bb_pad[i*1 + j*4 + 2]);

	for (int i = 0; i < 1; i++) {
	  int16_t aa_pad_line[1];

	for (int l = 0; l < 1 / 4; l++)
	    read_and_pad(&aa[i*A_stride + l*4], (int32_t *) &aa_pad_line[l*4], (int32_t *) &aa_pad_line[l*4 + 2]);

	for (int j = 0; j < 1; j++) {
	int32_t *aa_ptr = (int32_t *) aa_pad_line;
	int32_t *bb_ptr = (int32_t *) &bb_pad[j*1];
	int32_t sum = 0;

	for (int l = 0; l < 2 * (1 / 4); l++) {
	      sum = __smlad(*aa_ptr, *bb_ptr, sum);
	      ++aa_ptr; ++bb_ptr;
	}
	    /* NOTE: this is the line where `*_body` differs from `*_update`. here */
	    /* we're *setting* the result, instead of accumulating, because we know */
	    /* the `i` and `j` itervars span their entire respective axes. */
	    cc[i*C_stride + j] = sum;
	}
	}

	if (1 % 4 != 0)
	  gemm_1x1_body_rest_BFAJQBRS(1, aa, bb, cc, A_stride, B_stride, C_stride);

out:
	return retcode;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1_update_rest_BFAJQBRS(
	  int32_t K_arg,
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int K = K_arg;
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int k_base = (K / 4) * 4;

	switch (K % 4) {
	case 1:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] += (int32_t) a_ptr[0] * (int32_t) b_ptr[0];
	}
	}
	break;
	case 2:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] +=   (int32_t) a_ptr[0] * (int32_t) b_ptr[0]
				      + (int32_t) a_ptr[1] * (int32_t) b_ptr[1];
	}
	}
	break;
	case 3:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] +=   (int32_t) a_ptr[0] * (int32_t) b_ptr[0]
				      + (int32_t) a_ptr[1] * (int32_t) b_ptr[1]
				      + (int32_t) a_ptr[2] * (int32_t) b_ptr[2];
	}
	}
	break;
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_update_loop_BFAJQBRS(
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int32_t sum = 0;

	for (int l = 0; l < 1; l++) {
	      sum += (int32_t) aa[i*A_stride + l] * (int32_t) bb[j*B_stride + l];
	}
	    cc[i*C_stride + j] += sum;
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_update_BFAJQBRS(
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int16_t bb_pad[1];
	int32_t retcode = 0;

	if (1 < 2 && 1 < 2) {
	  retcode = gemm_1x1x1_update_loop_BFAJQBRS(aa, bb, cc, A_stride, B_stride, C_stride);
	goto out;
	}

	for (int i = 0; i < 1; i++)
	for (int j = 0; j < 1 / 4; j++)
	    read_and_pad(&bb[i*B_stride + j*4], (int32_t *) &bb_pad[i*1 + j*4], (int32_t *) &bb_pad[i*1 + j*4 + 2]);

	for (int i = 0; i < 1; i++) {
	  int16_t aa_pad_line[1];

	for (int l = 0; l < 1 / 4; l++)
	    read_and_pad(&aa[i*A_stride + l*4], (int32_t *) &aa_pad_line[l*4], (int32_t *) &aa_pad_line[l*4 + 2]);

	for (int j = 0; j < 1; j++) {
	int32_t *aa_ptr = (int32_t *) aa_pad_line;
	int32_t *bb_ptr = (int32_t *) &bb_pad[j*1];
	int32_t sum = 0;

	for (int l = 0; l < 2 * (1 / 4); l++) {
	      sum = __smlad(*aa_ptr, *bb_ptr, sum);
	      ++aa_ptr; ++bb_ptr;
	}
	    cc[i*C_stride + j] += sum;
	}
	}

	if (1 % 4 != 0)
	  gemm_1x1_update_rest_BFAJQBRS(1, aa, bb, cc, A_stride, B_stride, C_stride);

out:
	return retcode;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1_body_rest_BFAJQBRS(
	  int32_t K_arg,
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int K = K_arg;
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int k_base = (K / 2) * 2;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int16_t *a_ptr = &aa[i * A_stride + k_base];
	int16_t *b_ptr = &bb[j * B_stride + k_base];

	    cc[i * C_stride + j] = (int32_t) a_ptr[0] * (int32_t) b_ptr[0];
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1x1_body_loop_BFAJQBRS(
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int32_t sum = 0;

	for (int l = 0; l < 1; l++) {
	      sum += (int32_t) aa[i*A_stride + l] * (int32_t) bb[j*B_stride + l];
	}
	    /* NOTE: this is the line where `*_body` differs from `*_update`. here */
	    /* we're *setting* the result, instead of accumulating, because we know */
	    /* the `i` and `j` itervars span their entire respective axes. */
	    cc[i*C_stride + j] = sum;
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1x1_body_BFAJQBRS(
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int32_t retcode = 0;

	if (1 < 2 && 1 < 2) {
	  retcode = gemm16_1x1x1_body_loop_BFAJQBRS(aa, bb, cc, A_stride, B_stride, C_stride);
	goto out;
	}

	if (((uint32_t)aa & 0x3) != 0 || ((uint32_t)bb & 0x3) != 0) {
	  retcode = kTvmErrorFunctionCallInvalidArg;
	goto out;
	}

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	    int32_t aa_vector[1 / 2];
	    int32_t bb_vector[1 / 2];

	    memcpy(&aa_vector, &aa[i * A_stride], sizeof(aa_vector));
	    memcpy(&bb_vector, &bb[j * B_stride], sizeof(bb_vector));

	int32_t sum = 0;

	for (int l = 0; l < 1 / 2; l++) {
	      sum = __smlad(aa_vector[l], bb_vector[l], sum);
	}
	    /* NOTE: this is the line where `*_body` differs from `*_update`. here */
	    /* we're *setting* the result, instead of accumulating, because we know */
	    /* the `i` and `j` itervars span their entire respective axes. */
	    cc[i*C_stride + j] = sum;
	}
	}

	if (1 % 2 != 0)
	  gemm16_1x1_body_rest_BFAJQBRS(1, aa, bb, cc, A_stride, B_stride, C_stride);

out:
	return retcode;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1_update_rest_BFAJQBRS(
	  int32_t K_arg,
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int K = K_arg;
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int k_base = (K / 2) * 2;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int16_t *a_ptr = &aa[i * A_stride + k_base];
	int16_t *b_ptr = &bb[j * B_stride + k_base];

	    cc[i * C_stride + j] += (int32_t) a_ptr[0] * (int32_t) b_ptr[0];
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1x1_update_loop_BFAJQBRS(
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int32_t sum = 0;

	for (int l = 0; l < 1; l++) {
	      sum += (int32_t) aa[i*A_stride + l] * (int32_t) bb[j*B_stride + l];
	}
	    cc[i*C_stride + j] += sum;
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1x1_update_BFAJQBRS(
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int32_t retcode = 0;

	if (1 < 2 && 1 < 2) {
	  retcode = gemm16_1x1x1_update_loop_BFAJQBRS(aa, bb, cc, A_stride, B_stride, C_stride);
	goto out;
	}

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	    int32_t aa_vector[1 / 2];
	    int32_t bb_vector[1 / 2];

	    memcpy(&aa_vector, &aa[i * A_stride], sizeof(aa_vector));
	    memcpy(&bb_vector, &bb[j * B_stride], sizeof(bb_vector));

	int32_t sum = 0;

	for (int l = 0; l < 1 / 2; l++) {
	      sum = __smlad(aa_vector[l], bb_vector[l], sum);
	}
	    cc[i*C_stride + j] += sum;
	}
	}

	if (1 % 2 != 0)
	  gemm16_1x1_update_rest_BFAJQBRS(1, aa, bb, cc, A_stride, B_stride, C_stride);

out:
	return retcode;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_reset_BFAJQBRS(int32_t *cc, int32_t C_stride)
{
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	    cc[i*C_stride + j] = 0;
	}
	}
	return 0;
}



#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <arm_acle.h>

#include <tvm/runtime/crt/error_codes.h>


#ifndef ARM_CPU_INTRINSICS_EXIST
#define ARM_CPU_INTRINSICS_EXIST
__attribute__((always_inline)) uint32_t __ror(uint32_t op1, uint32_t op2)
{
	op2 %= 32U;
	if (op2 == 0U) {
	return op1;
	}
	return (op1 >> op2) | (op1 << (32U - op2));
}

#define __pkhbt(ARG1, ARG2, ARG3) __extension__ ({                            uint32_t __RES, __ARG1 = (ARG1), __ARG2 = (ARG2);   __asm("pkhbt %0, %1, %2, lsl %3" : "=r" (__RES) :  "r" (__ARG1), "r" (__ARG2), "I" (ARG3));   __RES;  })

#define __pkhtb(ARG1, ARG2, ARG3) __extension__ ({                            uint32_t __RES, __ARG1 = (ARG1), __ARG2 = (ARG2);   if (ARG3 == 0)     __asm("pkhtb %0, %1, %2" : "=r" (__RES) :  "r" (__ARG1), "r" (__ARG2));   else     __asm("pkhtb %0, %1, %2, asr %3" : "=r" (__RES) :  "r" (__ARG1), "r" (__ARG2), "I" (ARG3));   __RES;  })
#endif

#ifndef ARM_CPU_MPROFILE_READ_AND_PAD_EXISTS
#define ARM_CPU_MPROFILE_READ_AND_PAD_EXISTS
__attribute__((always_inline)) static inline const int8_t *read_and_pad(const int8_t *source, int32_t *out1, int32_t *out2)
{
	int32_t inA;

	  memcpy(&inA, source, 4);
	  source += 4;

	int32_t inAbuf1 = __sxtb16(__ror((uint32_t)inA, 8));
	int32_t inAbuf2 = __sxtb16(inA);
	  *out2 = (int32_t)(__pkhtb(inAbuf1, inAbuf2, 16));
	  *out1 = (int32_t)(__pkhbt(inAbuf2, inAbuf1, 16));

	return source;
}
#endif



#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1_body_rest_XTSTRCZP(
	  int32_t K_arg,
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int K = K_arg;
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int k_base = (K / 4) * 4;

	switch (K % 4) {
	case 1:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] = (int32_t) a_ptr[0] * (int32_t) b_ptr[0];
	}
	}
	break;
	case 2:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] =   (int32_t) a_ptr[0] * (int32_t) b_ptr[0]
				     + (int32_t) a_ptr[1] * (int32_t) b_ptr[1];
	}
	}
	break;
	case 3:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] =   (int32_t) a_ptr[0] * (int32_t) b_ptr[0]
				     + (int32_t) a_ptr[1] * (int32_t) b_ptr[1]
				     + (int32_t) a_ptr[2] * (int32_t) b_ptr[2];
	}
	}
	break;
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_body_loop_XTSTRCZP(
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;


	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int32_t sum = 0;

	for (int l = 0; l < 1; l++) {
	      sum += (int32_t) aa[i*A_stride + l] * (int32_t) bb[j*B_stride + l];
	}
	    /* NOTE: this is the line where `*_body` differs from `*_update`. here */
	    /* we're *setting* the result, instead of accumulating, because we know */
	    /* the `i` and `j` itervars span their entire respective axes. */
	    cc[i*C_stride + j] = sum;
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_body_XTSTRCZP(
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int16_t bb_pad[1];
	int32_t retcode = 0;

	if (1 < 2 && 1 < 2) {
	  retcode = gemm_1x1x1_body_loop_XTSTRCZP(aa, bb, cc, A_stride, B_stride, C_stride);
	goto out;
	}

	for (int i = 0; i < 1; i++)
	for (int j = 0; j < 1 / 4; j++)
	    read_and_pad(&bb[i*B_stride + j*4], (int32_t *) &bb_pad[i*1 + j*4], (int32_t *) &bb_pad[i*1 + j*4 + 2]);

	for (int i = 0; i < 1; i++) {
	  int16_t aa_pad_line[1];

	for (int l = 0; l < 1 / 4; l++)
	    read_and_pad(&aa[i*A_stride + l*4], (int32_t *) &aa_pad_line[l*4], (int32_t *) &aa_pad_line[l*4 + 2]);

	for (int j = 0; j < 1; j++) {
	int32_t *aa_ptr = (int32_t *) aa_pad_line;
	int32_t *bb_ptr = (int32_t *) &bb_pad[j*1];
	int32_t sum = 0;

	for (int l = 0; l < 2 * (1 / 4); l++) {
	      sum = __smlad(*aa_ptr, *bb_ptr, sum);
	      ++aa_ptr; ++bb_ptr;
	}
	    /* NOTE: this is the line where `*_body` differs from `*_update`. here */
	    /* we're *setting* the result, instead of accumulating, because we know */
	    /* the `i` and `j` itervars span their entire respective axes. */
	    cc[i*C_stride + j] = sum;
	}
	}

	if (1 % 4 != 0)
	  gemm_1x1_body_rest_XTSTRCZP(1, aa, bb, cc, A_stride, B_stride, C_stride);

out:
	return retcode;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1_update_rest_XTSTRCZP(
	  int32_t K_arg,
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int K = K_arg;
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int k_base = (K / 4) * 4;

	switch (K % 4) {
	case 1:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] += (int32_t) a_ptr[0] * (int32_t) b_ptr[0];
	}
	}
	break;
	case 2:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] +=   (int32_t) a_ptr[0] * (int32_t) b_ptr[0]
				      + (int32_t) a_ptr[1] * (int32_t) b_ptr[1];
	}
	}
	break;
	case 3:
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int8_t *a_ptr = &aa[i * A_stride + k_base];
	int8_t *b_ptr = &bb[j * B_stride + k_base];

	      cc[i * C_stride + j] +=   (int32_t) a_ptr[0] * (int32_t) b_ptr[0]
				      + (int32_t) a_ptr[1] * (int32_t) b_ptr[1]
				      + (int32_t) a_ptr[2] * (int32_t) b_ptr[2];
	}
	}
	break;
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_update_loop_XTSTRCZP(
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int32_t sum = 0;

	for (int l = 0; l < 1; l++) {
	      sum += (int32_t) aa[i*A_stride + l] * (int32_t) bb[j*B_stride + l];
	}
	    cc[i*C_stride + j] += sum;
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_update_XTSTRCZP(
	  int8_t *aa, int8_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int16_t bb_pad[1];
	int32_t retcode = 0;

	if (1 < 2 && 1 < 2) {
	  retcode = gemm_1x1x1_update_loop_XTSTRCZP(aa, bb, cc, A_stride, B_stride, C_stride);
	goto out;
	}

	for (int i = 0; i < 1; i++)
	for (int j = 0; j < 1 / 4; j++)
	    read_and_pad(&bb[i*B_stride + j*4], (int32_t *) &bb_pad[i*1 + j*4], (int32_t *) &bb_pad[i*1 + j*4 + 2]);

	for (int i = 0; i < 1; i++) {
	  int16_t aa_pad_line[1];

	for (int l = 0; l < 1 / 4; l++)
	    read_and_pad(&aa[i*A_stride + l*4], (int32_t *) &aa_pad_line[l*4], (int32_t *) &aa_pad_line[l*4 + 2]);

	for (int j = 0; j < 1; j++) {
	int32_t *aa_ptr = (int32_t *) aa_pad_line;
	int32_t *bb_ptr = (int32_t *) &bb_pad[j*1];
	int32_t sum = 0;

	for (int l = 0; l < 2 * (1 / 4); l++) {
	      sum = __smlad(*aa_ptr, *bb_ptr, sum);
	      ++aa_ptr; ++bb_ptr;
	}
	    cc[i*C_stride + j] += sum;
	}
	}

	if (1 % 4 != 0)
	  gemm_1x1_update_rest_XTSTRCZP(1, aa, bb, cc, A_stride, B_stride, C_stride);

out:
	return retcode;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1_body_rest_XTSTRCZP(
	  int32_t K_arg,
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int K = K_arg;
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int k_base = (K / 2) * 2;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int16_t *a_ptr = &aa[i * A_stride + k_base];
	int16_t *b_ptr = &bb[j * B_stride + k_base];

	    cc[i * C_stride + j] = (int32_t) a_ptr[0] * (int32_t) b_ptr[0];
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1x1_body_loop_XTSTRCZP(
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int32_t sum = 0;

	for (int l = 0; l < 1; l++) {
	      sum += (int32_t) aa[i*A_stride + l] * (int32_t) bb[j*B_stride + l];
	}
	    /* NOTE: this is the line where `*_body` differs from `*_update`. here */
	    /* we're *setting* the result, instead of accumulating, because we know */
	    /* the `i` and `j` itervars span their entire respective axes. */
	    cc[i*C_stride + j] = sum;
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1x1_body_XTSTRCZP(
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int32_t retcode = 0;

	if (1 < 2 && 1 < 2) {
	  retcode = gemm16_1x1x1_body_loop_XTSTRCZP(aa, bb, cc, A_stride, B_stride, C_stride);
	goto out;
	}

	if (((uint32_t)aa & 0x3) != 0 || ((uint32_t)bb & 0x3) != 0) {
	  retcode = kTvmErrorFunctionCallInvalidArg;
	goto out;
	}

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	    int32_t aa_vector[1 / 2];
	    int32_t bb_vector[1 / 2];

	    memcpy(&aa_vector, &aa[i * A_stride], sizeof(aa_vector));
	    memcpy(&bb_vector, &bb[j * B_stride], sizeof(bb_vector));

	int32_t sum = 0;

	for (int l = 0; l < 1 / 2; l++) {
	      sum = __smlad(aa_vector[l], bb_vector[l], sum);
	}
	    /* NOTE: this is the line where `*_body` differs from `*_update`. here */
	    /* we're *setting* the result, instead of accumulating, because we know */
	    /* the `i` and `j` itervars span their entire respective axes. */
	    cc[i*C_stride + j] = sum;
	}
	}

	if (1 % 2 != 0)
	  gemm16_1x1_body_rest_XTSTRCZP(1, aa, bb, cc, A_stride, B_stride, C_stride);

out:
	return retcode;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1_update_rest_XTSTRCZP(
	  int32_t K_arg,
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int K = K_arg;
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int k_base = (K / 2) * 2;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int16_t *a_ptr = &aa[i * A_stride + k_base];
	int16_t *b_ptr = &bb[j * B_stride + k_base];

	    cc[i * C_stride + j] += (int32_t) a_ptr[0] * (int32_t) b_ptr[0];
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1x1_update_loop_XTSTRCZP(
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	int32_t sum = 0;

	for (int l = 0; l < 1; l++) {
	      sum += (int32_t) aa[i*A_stride + l] * (int32_t) bb[j*B_stride + l];
	}
	    cc[i*C_stride + j] += sum;
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm16_1x1x1_update_XTSTRCZP(
	  int16_t *aa, int16_t *bb, int32_t *cc,
	  int32_t A_stride_arg, int32_t B_stride_arg, int32_t C_stride_arg) {
	int A_stride = A_stride_arg;
	int B_stride = B_stride_arg;
	int C_stride = C_stride_arg;

	int32_t retcode = 0;

	if (1 < 2 && 1 < 2) {
	  retcode = gemm16_1x1x1_update_loop_XTSTRCZP(aa, bb, cc, A_stride, B_stride, C_stride);
	goto out;
	}

	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	    int32_t aa_vector[1 / 2];
	    int32_t bb_vector[1 / 2];

	    memcpy(&aa_vector, &aa[i * A_stride], sizeof(aa_vector));
	    memcpy(&bb_vector, &bb[j * B_stride], sizeof(bb_vector));

	int32_t sum = 0;

	for (int l = 0; l < 1 / 2; l++) {
	      sum = __smlad(aa_vector[l], bb_vector[l], sum);
	}
	    cc[i*C_stride + j] += sum;
	}
	}

	if (1 % 2 != 0)
	  gemm16_1x1_update_rest_XTSTRCZP(1, aa, bb, cc, A_stride, B_stride, C_stride);

out:
	return retcode;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__((always_inline)) static inline int32_t gemm_1x1x1_reset_XTSTRCZP(int32_t *cc, int32_t C_stride)
{
	for (int i = 0; i < 1; i++) {
	for (int j = 0; j < 1; j++) {
	    cc[i*C_stride + j] = 0;
	}
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value, int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value, int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value, int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_quantized_fused_reshape(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value, int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_quantized_fused_reshape_1(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value, int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t gemm_1x1x1_reset_QYKAYUUR(int32_t*, int32_t);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t gemm_1x1x1_update_QYKAYUUR(int8_t*, int8_t*, int32_t*, int32_t, int32_t, int32_t);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t gemm_1x1x1_reset_BFAJQBRS(int32_t*, int32_t);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t gemm_1x1x1_update_BFAJQBRS(int8_t*, int8_t*, int32_t*, int32_t, int32_t, int32_t);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t gemm_1x1x1_reset_XTSTRCZP(int32_t*, int32_t);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t gemm_1x1x1_update_XTSTRCZP(int8_t*, int8_t*, int32_t*, int32_t, int32_t, int32_t);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value, int32_t *out_ret_tcode, void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *p1 = (((TVMValue *)args)[1].v_handle);
	void *p2 = (((TVMValue *)args)[2].v_handle);
	void *p3 = (((TVMValue *)args)[3].v_handle);
	void *p4 = (((TVMValue *)args)[4].v_handle);
	void *T_cast = (((TVMValue *)args)[5].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_p0_strides = (((DLTensor *)p0)[0].strides);
	void *p1_1 = (((DLTensor *)p1)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_p1_strides = (((DLTensor *)p1)[0].strides);
	void *p2_1 = (((DLTensor *)p2)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_p2_strides = (((DLTensor *)p2)[0].strides);
	void *p3_1 = (((DLTensor *)p3)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_p3_strides = (((DLTensor *)p3)[0].strides);
	void *p4_1 = (((DLTensor *)p4)[0].data);
	void *T_cast_1 = (((DLTensor *)T_cast)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_T_cast_strides = (((DLTensor *)T_cast)[0].strides);

	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_p0_strides == NULL)) {
	}
	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_p1_strides == NULL)) {
	}
	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_p2_strides == NULL)) {
	}
	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_p3_strides == NULL)) {
	}
	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_T_cast_strides == NULL)) {
	}
	int32_t dense[16];

	for (int32_t y_outer = 0; y_outer < 16; ++y_outer) {
	  gemm_1x1x1_reset_QYKAYUUR((&(dense[y_outer])), 1);
	  gemm_1x1x1_update_QYKAYUUR((&(((int8_t *)p0_1)[0])), (&(((int8_t *)p1_1)[y_outer])), (&(dense[y_outer])), 1, 1, 1);
	}
	for (int32_t ax1 = 0; ax1 < 16; ++ax1) {
	int32_t v_ = ((int32_t *)p4_1)[0] + ((int32_t)(((((0 != 0) ? (((int64_t)((dense[ax1] + ((int32_t *)p3_1)[ax1]) - ((int32_t *)p2_1)[ax1])) << ((int64_t)0)) : ((int64_t)((dense[ax1] + ((int32_t *)p3_1)[ax1]) - ((int32_t *)p2_1)[ax1]))) * (int64_t)1169592283) + ((int64_t)1 << ((int64_t)((6 + 31) - 1)))) >> ((int64_t)(6 + 31))));
	int32_t v__1 = (v_) < (127) ? (v_) : (127);
	  ((int8_t *)T_cast_1)[ax1] = ((int8_t)((v__1) > (-128) ? (v__1) : (-128)));
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value, int32_t *out_ret_tcode, void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *p1 = (((TVMValue *)args)[1].v_handle);
	void *p2 = (((TVMValue *)args)[2].v_handle);
	void *p3 = (((TVMValue *)args)[3].v_handle);
	void *p4 = (((TVMValue *)args)[4].v_handle);
	void *T_cast = (((TVMValue *)args)[5].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1_p0_strides = (((DLTensor *)p0)[0].strides);
	void *p1_1 = (((DLTensor *)p1)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1_p1_strides = (((DLTensor *)p1)[0].strides);
	void *p2_1 = (((DLTensor *)p2)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1_p2_strides = (((DLTensor *)p2)[0].strides);
	void *p3_1 = (((DLTensor *)p3)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1_p3_strides = (((DLTensor *)p3)[0].strides);
	void *p4_1 = (((DLTensor *)p4)[0].data);
	void *T_cast_1 = (((DLTensor *)T_cast)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1_T_cast_strides = (((DLTensor *)T_cast)[0].strides);

	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1_p0_strides == NULL)) {
	}
	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1_p1_strides == NULL)) {
	}
	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1_p2_strides == NULL)) {
	}
	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1_p3_strides == NULL)) {
	}
	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1_T_cast_strides == NULL)) {
	}
	int32_t dense[16];

	for (int32_t y_outer = 0; y_outer < 16; ++y_outer) {
	  gemm_1x1x1_reset_BFAJQBRS((&(dense[y_outer])), 1);
	for (int32_t k_outer = 0; k_outer < 16; ++k_outer) {
	    gemm_1x1x1_update_BFAJQBRS((&(((int8_t *)p0_1)[k_outer])), (&(((int8_t *)p1_1)[((y_outer * 16) + k_outer)])), (&(dense[y_outer])), 1, 1, 1);
	}
	}
	for (int32_t ax1 = 0; ax1 < 16; ++ax1) {
	int32_t v_ = ((int32_t *)p4_1)[0] + ((int32_t)(((((0 != 0) ? (((int64_t)((dense[ax1] + ((int32_t *)p3_1)[ax1]) - ((int32_t *)p2_1)[ax1])) << ((int64_t)0)) : ((int64_t)((dense[ax1] + ((int32_t *)p3_1)[ax1]) - ((int32_t *)p2_1)[ax1]))) * (int64_t)1799926384) + ((int64_t)1 << ((int64_t)((5 + 31) - 1)))) >> ((int64_t)(5 + 31))));
	int32_t v__1 = (v_) < (127) ? (v_) : (127);
	  ((int8_t *)T_cast_1)[ax1] = ((int8_t)((v__1) > (-128) ? (v__1) : (-128)));
	}
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value, int32_t *out_ret_tcode, void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *p1 = (((TVMValue *)args)[1].v_handle);
	void *p2 = (((TVMValue *)args)[2].v_handle);
	void *p3 = (((TVMValue *)args)[3].v_handle);
	void *T_cast = (((TVMValue *)args)[4].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2_p0_strides = (((DLTensor *)p0)[0].strides);
	void *p1_1 = (((DLTensor *)p1)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2_p1_strides = (((DLTensor *)p1)[0].strides);
	void *p2_1 = (((DLTensor *)p2)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2_p2_strides = (((DLTensor *)p2)[0].strides);
	void *p3_1 = (((DLTensor *)p3)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2_p3_strides = (((DLTensor *)p3)[0].strides);
	void *T_cast_1 = (((DLTensor *)T_cast)[0].data);
	void *tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2_T_cast_strides = (((DLTensor *)T_cast)[0].strides);

	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2_p0_strides == NULL)) {
	}
	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2_p1_strides == NULL)) {
	}
	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2_p2_strides == NULL)) {
	}
	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2_p3_strides == NULL)) {
	}
	if (!(tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2_T_cast_strides == NULL)) {
	}
	int32_t dense[1];

	gemm_1x1x1_reset_XTSTRCZP((&(dense[0])), 1);
	for (int32_t k_outer = 0; k_outer < 16; ++k_outer) {
	  gemm_1x1x1_update_XTSTRCZP((&(((int8_t *)p0_1)[k_outer])), (&(((int8_t *)p1_1)[k_outer])), (&(dense[0])), 1, 1, 1);
	}
	int32_t v_ = ((int32_t)(((((0 != 0) ? (((int64_t)((dense[0] + ((int32_t *)p3_1)[0]) - ((int32_t *)p2_1)[0])) << ((int64_t)0)) : ((int64_t)((dense[0] + ((int32_t *)p3_1)[0]) - ((int32_t *)p2_1)[0]))) * (int64_t)1623168516) + ((int64_t)1 << ((int64_t)((7 + 31) - 1)))) >> ((int64_t)(7 + 31)))) + 4;
	int32_t v__1 = (v_) < (127) ? (v_) : (127);
	((int8_t *)T_cast_1)[0] = ((int8_t)((v__1) > (-128) ? (v__1) : (-128)));
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_quantized_fused_reshape(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value, int32_t *out_ret_tcode, void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *T_reshape = (((TVMValue *)args)[1].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *tvmgen_quantized_fused_reshape_p0_strides = (((DLTensor *)p0)[0].strides);
	void *T_reshape_1 = (((DLTensor *)T_reshape)[0].data);
	void *tvmgen_quantized_fused_reshape_T_reshape_strides = (((DLTensor *)T_reshape)[0].strides);

	if (!(tvmgen_quantized_fused_reshape_p0_strides == NULL)) {
	}
	if (!(tvmgen_quantized_fused_reshape_T_reshape_strides == NULL)) {
	}
	((int8_t *)T_reshape_1)[0] = ((int8_t *)p0_1)[0];
	return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_quantized_fused_reshape_1(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value, int32_t *out_ret_tcode, void *resource_handle)
{
	void *p0 = (((TVMValue *)args)[0].v_handle);
	void *T_reshape = (((TVMValue *)args)[1].v_handle);
	void *p0_1 = (((DLTensor *)p0)[0].data);
	void *tvmgen_quantized_fused_reshape_1_p0_strides = (((DLTensor *)p0)[0].strides);
	void *T_reshape_1 = (((DLTensor *)T_reshape)[0].data);
	void *tvmgen_quantized_fused_reshape_1_T_reshape_strides = (((DLTensor *)T_reshape)[0].strides);

	if (!(tvmgen_quantized_fused_reshape_1_p0_strides == NULL)) {
	}
	if (!(tvmgen_quantized_fused_reshape_1_T_reshape_strides == NULL)) {
	}
	for (int32_t ax1_inner = 0; ax1_inner < 16; ++ax1_inner) {
	  ((int8_t *)T_reshape_1)[ax1_inner] = ((int8_t *)p0_1)[ax1_inner];
	}
	return 0;
}
