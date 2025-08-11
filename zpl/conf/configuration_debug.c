/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/configuration.h>

#include <zephyr/kernel.h>

#define ZPL_WAIT_FOR_CONF_DEF(name, config)                 \
	void zpl_wait_for_##name(void)                            \
	{                                                         \
		while (!IS_ENABLED(config) && !debug_configs.name) {    \
			k_msleep(100);                                        \
		}                                                       \
	}

#define ZPL_CHECK_IF_CONF_DEF(name, config)                 \
	bool zpl_check_if_conf_##name(void)                       \
	{                                                         \
		return IS_ENABLED(config) || debug_configs.name;        \
	}

#define ZPL_CONF_DEBUG_STRUCT_FIELD_DEF(name) bool name
#define ZPL_CONF_DEBUG_DEF(name, config)   \
	ZPL_WAIT_FOR_CONF_DEF(name, config)      \
	ZPL_CHECK_IF_CONF_DEF(name, config)

struct runtime_configs {
	/* Struct fields definitions */
	ZPL_CONF_DEBUG_STRUCT_FIELD_DEF(mem_usage_trace);
};

static struct runtime_configs volatile debug_configs;

/* Config definitions */
ZPL_CONF_DEBUG_DEF(mem_usage_trace, CONFIG_ZPL_MEMORY_USAGE_TRACE)
