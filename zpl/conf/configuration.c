/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/configuration.h>

#define ZPL_CONF_THREADING_VARIABLES(name)        \
	K_MUTEX_DEFINE(zpl_conf_##name##_lock);       \
	K_CONDVAR_DEFINE(zpl_conf_##name##_condvar);  \

#define ZPL_CONF_WAIT_DEFINE_0(name) void zpl_conf_wait_##name(void) {}
#define ZPL_CONF_WAIT_DEFINE_1(name)                                                        \
	void zpl_conf_wait_##name(void)                                                         \
	{                                                                                       \
		k_mutex_lock(&zpl_conf_##name##_lock, K_FOREVER);                                   \
		if (!debug_configs.name) {                                                          \
			k_condvar_wait(&zpl_conf_##name##_condvar, &zpl_conf_##name##_lock, K_FOREVER); \
		}                                                                                   \
		k_mutex_unlock(&zpl_conf_##name##_lock);                                            \
	}
#define ZPL_CONF_WAIT_DEFINE(name, threading) CONCAT(ZPL_CONF_WAIT_DEFINE_, threading)(name)

#define ZPL_CONF_IS_ENABLED_DEFINE_0(name) \
	bool zpl_conf_is_enabled_##name(void)  \
	{                                      \
		return debug_configs.name;         \
	}
#define ZPL_CONF_IS_ENABLED_DEFINE_1(name)                \
	bool zpl_conf_is_enabled_##name(void)                 \
	{                                                     \
		k_mutex_lock(&zpl_conf_##name##_lock, K_FOREVER); \
		bool state = debug_configs.name;                  \
		k_mutex_unlock(&zpl_conf_##name##_lock);          \
		return state;                                     \
	}
#define ZPL_CONF_IS_ENABLED_DEFINE(name, threading) CONCAT(ZPL_CONF_IS_ENABLED_DEFINE_, threading)(name)

#define ZPL_CONF_SET_DEFINE_0(name)        \
	void zpl_conf_set_##name(bool state)   \
	{                                      \
		debug_configs.name = state;        \
	}
#define ZPL_CONF_SET_DEFINE_1(name)                       \
	void zpl_conf_set_##name(bool state)                  \
	{                                                     \
		k_mutex_lock(&zpl_conf_##name##_lock, K_FOREVER); \
		debug_configs.name = state;                       \
		if (debug_configs.name) {                         \
			k_condvar_signal(&zpl_conf_##name##_condvar); \
		}                                                 \
		k_mutex_unlock(&zpl_conf_##name##_lock);          \
	}
#define ZPL_CONF_SET_DEFINE(name, threading) CONCAT(ZPL_CONF_SET_DEFINE_, threading)(name)

#define DECLARE_CONF_FLAG(name, ...) bool name;
#define DEFINE_CONF_FLAG(name, ...) .name = true,

struct configs { CONFIGS(DECLARE_CONF_FLAG) };
volatile struct configs debug_configs = { CONFIGS(DEFINE_CONF_FLAG) };

#undef DECLARE_CONF_FLAG
#undef DEFINE_CONF_FLAG

#define ZPL_CONF_DEFINE(name, threading, ...)                          \
	ZPL_IMPL_IF_ENABLED(threading, ZPL_CONF_THREADING_VARIABLES)(name) \
	ZPL_CONF_IS_ENABLED_DEFINE(name, threading)                        \
	ZPL_CONF_WAIT_DEFINE(name, threading)                              \
	ZPL_CONF_SET_DEFINE(name, threading)

CONFIGS(ZPL_CONF_DEFINE)
