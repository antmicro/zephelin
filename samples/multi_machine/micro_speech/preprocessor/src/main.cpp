/*
 * Copyright (c) 2026 Analog Devices, Inc.
 * Copyright (c) 2026 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/drivers/uart.h>
#include <zpl.h>
#include <zpl/time.h>
#include <tflm_model.h>
#include <string.h>

#include "no_1000ms.h"
const int g_audio_sample_size = sizeof(g_audio_sample) / sizeof(g_audio_sample[0]);

extern "C" {
  #include <generated/model0_data.h>
}

#define SAMPLE_RATE_HZ 16000
#define WINDOW_STRIDE_MS 20
#define STRIDE_SAMPLES ((SAMPLE_RATE_HZ * WINDOW_STRIDE_MS) / 1000)

ZPL_CODE_SCOPE_DEFINE(send_frame, true);

#define INPUT_SHAPE 480
#define OUTPUT_SHAPE 40

static int16_t input_buffer[INPUT_SHAPE];
static int8_t model_output[OUTPUT_SHAPE];

const struct device *uart_dev = DEVICE_DT_GET(DT_NODELABEL(uart1));

#define EXTERNAL_CLOCK_ADDR 0x400FFFF0

using namespace tflm;

static uint64_t cycles_get(void)
{
	return (uint64_t)*(volatile uint32_t *)EXTERNAL_CLOCK_ADDR;
}

static uint64_t timestamp_get(uint64_t cycles)
{
    return cycles * 1000ULL;
}

static zpl_clock_t custom_clock = {
	.cycles_get = cycles_get,
	.timestamp_get = timestamp_get,
};

void generate_input();
void send_data_via_uart(int8_t data[]);

int main(void)
{
  int status = 0;
  printk("PREPROCESSOR STATRING...\n");

  zpl_clock_set(custom_clock);
  zpl_init();

  // Give micro-speech time to initialize
  k_msleep(1000);

	model_init();

	status = model_load(model0_data);
	if (status) {
		printk("Model load failed %d\n", status);
		return 1;
	}

  for(;;) {

    generate_input();

    status = model_load_input((uint8_t *)input_buffer, sizeof(int16_t) * INPUT_SHAPE);

    if (status) {
      printk("Model load input failed %d\n", status);
      return 1;
    }

    status = model_run();
    if (status) {
        printk("Model invocation failed\n");
        return 1;
    }

    status = model_get_output((uint8_t *)model_output, sizeof(model_output));
    if (status) {
        printk("Model get output failed %d\n", status);
        return 1;
    }

    send_data_via_uart(model_output);
  }

  return 0;
}

void generate_input() {
  static int current_index = 0;

  int remaining_samples = g_audio_sample_size - current_index;
  int copy_size = (remaining_samples < INPUT_SHAPE) ? remaining_samples : INPUT_SHAPE;

  memcpy(input_buffer, &g_audio_sample[current_index], copy_size * sizeof(int16_t));

  if (copy_size < INPUT_SHAPE) {
    memset(input_buffer + copy_size, 0, (INPUT_SHAPE - copy_size) * sizeof(int16_t));
  }

  current_index += STRIDE_SAMPLES;

  if (current_index >= g_audio_sample_size) {
    current_index = 0;
  }
}

void send_data_via_uart(int8_t data[]) {
  // Send sync header
  uart_poll_out(uart_dev, 0xAA);
  uart_poll_out(uart_dev, 0xBB);

  // Send model output
  ZPL_MARK_CODE_SCOPE(send_frame) {
    for (int i = 0; i < OUTPUT_SHAPE; ++i) {
      uart_poll_out(uart_dev, (uint8_t)data[i]);
      k_usleep(100);
    }
  }

  // Send footer
  uart_poll_out(uart_dev, '\n');

}
