/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/configuration.h>

#include <zephyr/kernel.h>

#define ZPL_WAIT_FOR_CONF_DEF(name, define)  \
void zpl_wait_for_##name(void)               \
{                                            \
	if (!IS_ENABLED(define)) {                 \
		k_sleep(K_FOREVER);                      \
	}                                          \
}

#define ZPL_CHECK_IF_CONF_DEF(name, config)       \
	bool zpl_check_if_conf_##name(void)             \
	{                                               \
		return IS_ENABLED(config);                    \
	}

#define ZPL_CONF_NONE_DEF(name, config)   \
	ZPL_WAIT_FOR_CONF_DEF(name, config)     \
	ZPL_CHECK_IF_CONF_DEF(name, config)

/* Config definitions */
ZPL_CONF_NONE_DEF(mem_usage_trace, CONFIG_ZPL_MEMORY_USAGE_TRACE)
