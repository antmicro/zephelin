/*
 * Copyright (c) 2026 Analog Devices, Inc.
 * Copyright (c) 2026 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl.h>
#include <zephyr/kernel.h>
#include <zephyr/drivers/uart.h>
#include <tflm_model.h>

extern "C" {
  #include <generated/model0_data.h>
}

ZPL_CODE_SCOPE_DEFINE(send_frame, true);

#define INPUT_SHAPE 480
#define OUTPUT_SHAPE 40

static int16_t input_buffer[INPUT_SHAPE];
static int8_t model_output[OUTPUT_SHAPE];

const struct device *uart_dev = DEVICE_DT_GET(DT_NODELABEL(uart1));

using namespace tflm;

void generate_input();
void send_data_via_uart(int8_t data[]);

int main(void)
{
  int status = 0;
  printk("PREPROCESSOR STATRING...\n");

  // Give micro-speech time to initialize
  k_msleep(1000);

  zpl_init();
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
  // Put fake data into buffer
  for (int i = 0; i < INPUT_SHAPE; i++) {
    input_buffer[i] = (i % 100) * 50;
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
