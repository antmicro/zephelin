/*
 * Copyright (c) 2026 Analog Devices, Inc.
 * Copyright (c) 2026 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/sys/printk.h>
#include <zephyr/sys/ring_buffer.h>
#include <zpl.h>
#include <zpl/time.h>
#include <tflm_model.h>

extern "C" {
	#include <generated/model0_data.h>
}

#define INPUT_SHAPE 1960
#define OUTPUT_SHAPE 4

static int8_t input_buffer[INPUT_SHAPE];
static int8_t model_output[OUTPUT_SHAPE];
static int input_index = 0;

#define PAYLOAD_SIZE 40
static int8_t current_payload[PAYLOAD_SIZE];

#define RING_BUF_SIZE 4096
RING_BUF_DECLARE(uart_ringbuf, RING_BUF_SIZE);

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

void handle_inference_cycle();
void uart_interrupt_handler(const struct device *dev, void *user_data);
void process_uart_byte(uint8_t recv_byte);

int main(void)
{
	uint8_t recv_byte;
	int status = 0;

	zpl_clock_set(custom_clock);
	zpl_init();

	model_init();

	status = model_load(model0_data);
	if (status) {
		printk("Model load failed %d\n", status);
		return 1;
	}

	if (!device_is_ready(uart_dev)) {
		printk("RECEIVER ERROR: UART1 device not ready\n");
		return 0;
	}

	uart_irq_callback_set(uart_dev, uart_interrupt_handler);
	uart_irq_rx_enable(uart_dev);

	for (;;) {
		if (ring_buf_get(&uart_ringbuf, &recv_byte, 1) > 0) {
			process_uart_byte(recv_byte);
		} else {
			k_msleep(1);
		}
	}
	return 0;
}

void handle_inference_cycle() {
    printk("Buffer full. Running inference...\n");
    int status = 0;
    status = model_load_input((uint8_t *) input_buffer, sizeof(uint8_t) * INPUT_SHAPE);

    if (status) {
        printk("Model load input failed %d\n", status);
        return;
    }

    status = model_run();

    if (status) {
        printk("Model invocation failed %d\n", status);
        return;
    }

    status = model_get_output((uint8_t *)model_output, sizeof(model_output));
    if (status) {
        printk("Model get output failed %d\n", status);
        return;
    }

    printk("Inference complete. Results: \n");
    printk("silence: %d\n unknown: %d\n yes: %d\n no: %d\n",
           model_output[0],
           model_output[1],
           model_output[2],
           model_output[3]
    );

    input_index = 0;
}


void process_uart_byte(uint8 recv_byte) {
	static int bytes_read = 0;
	static enum State {
		WAIT_HEADER,
		WAIT_SYNC,
		PAYLOAD,
		FOOTER
	} state = WAIT_HEADER;

	switch (state) {
		case WAIT_HEADER:
			if (recv_byte == 0xAA) state = WAIT_SYNC;
			break;

		case WAIT_SYNC:
			if (recv_byte == 0xBB) {
				state = PAYLOAD;
				bytes_read = 0;
			} else if (recv_byte != 0xAA) {
				state = WAIT_HEADER;
			}
			break;

		case PAYLOAD:
			current_payload[bytes_read++] = (int8_t)recv_byte;
			if (bytes_read >= PAYLOAD_SIZE) state = FOOTER;
			break;

		case FOOTER:
			if (recv_byte == '\n') {
				for (int i = 0; i < PAYLOAD_SIZE && input_index < INPUT_SHAPE; i++) {
					input_buffer[input_index++] = current_payload[i];
				}

				if (input_index >= INPUT_SHAPE) {
					handle_inference_cycle();
				}
			} else {
				printk("Invalid frame footer: 0x%02X\n", recv_byte);
			}
			state = WAIT_HEADER;
			break;
	}
}

void uart_interrupt_handler(const struct device *dev, void *user_data) {
	uint8_t c;

	if(!uart_irq_update(dev)) {
		return;
	}

	if (!uart_irq_rx_ready(dev)) {
		return;
	}

    while (uart_fifo_read(dev, &c, 1) == 1) {
        ring_buf_put(&uart_ringbuf, &c, 1);
    }
}
