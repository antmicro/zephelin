/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <tracing_backend.h>
#include <stdint.h>

static void tracing_backend_trivial_uart_init(void)
{
	/* Empty */
}

static void tracing_backend_trivial_uart_output(
		const struct tracing_backend *backend, uint8_t *data, uint32_t length)
{
	for ( ; length--; data++) {
		*(volatile uint32_t *)0xD0000000 = *data;
	}
}

const struct tracing_backend_api tracing_backend_trivial_uart_api = {
	.init = tracing_backend_trivial_uart_init,
	.output = tracing_backend_trivial_uart_output
};

TRACING_BACKEND_DEFINE(tracing_backend_trivial_uart, tracing_backend_trivial_uart_api);
