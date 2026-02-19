/*
 * Copyright (c) 2025-2026 Analog Devices, Inc.
 * Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef SAMPLE_COMMON_TFLM_MOLDE_H_
#define SAMPLE_COMMON_TFLM_MOLDE_H_

#include <cstddef>
#include <stdint.h>
#include <tensorflow/lite/micro/micro_interpreter.h>

#define BASE_OPS_COUNT 5

#ifdef IS_PREPROCESSOR
	#define PREPROCESSOR_OPS_COUNT 17
#else
	#define PREPROCESSOR_OPS_COUNT 0
#endif

#ifdef IS_MICROSPEECH
	#define MICROSPEECH_OPS_COUNT 1
#else
	#define MICROSPEECH_OPS_COUNT 0
#endif

#define TFLITE_RESOLVER_SIZE (BASE_OPS_COUNT + PREPROCESSOR_OPS_COUNT + MICROSPEECH_OPS_COUNT)

namespace tflm {
void model_init(void);

int model_load(const uint8_t *model);
int model_load(const uint8_t *model, tflite::MicroInterpreter * &gp_interpreter);
int model_load(const uint8_t *model, tflite::MicroInterpreter * &gp_interpreter,
	size_t tensor_arena_size);

int model_load_input(const uint8_t *input, uint32_t input_size);
int model_load_input(tflite::MicroInterpreter * const gp_interpreter, const uint8_t *input,
	uint32_t input_size);

int model_run(void);
int model_run(tflite::MicroInterpreter * const gp_interpreter);

int model_get_output(uint8_t *output, uint32_t output_size);
int model_get_output(tflite::MicroInterpreter * const gp_interpreter, uint8_t *output,
	uint32_t output_size);
}

#endif /* SAMPLE_COMMON_TFLM_MOLDE_H_ */
