/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <stdint.h>

#define TFLITE_BUFFER_SIZE   40
#define TFLITE_RESOLVER_SIZE 5

void model_init(void);
int model_load(const uint8_t *model, uint32_t model_size);
int model_load_input(const uint8_t *input, uint32_t input_size);
int model_run(void);
int model_get_output(uint8_t *output, uint32_t output_size);
