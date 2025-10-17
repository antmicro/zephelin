/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef ZEPHYR_PROFILING_LIB_CONFIGURATION_H_
#define ZEPHYR_PROFILING_LIB_CONFIGURATION_H_

#include <stdbool.h>
#include <zephyr/kernel.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ZPL_NOOP(...)
#define ZPL_IMPL_0(CONFIG) ZPL_NOOP
#define ZPL_IMPL_1(CONFIG) CONFIG
#define ZPL_IMPL_IF_ENABLED(FLAG, CONFIG) \
	CONCAT(ZPL_IMPL_, IS_ENABLED(FLAG))(CONFIG)

#define CONFIGS(CONFIG)                                                          \
	ZPL_IMPL_IF_ENABLED(CONFIG_ZPL_MEMORY_PROFILING,    CONFIG)(memory_profiler, \
			IS_ENABLED(CONFIG_ZPL_MEMORY_PROFILING_CONF_THREADING))

#define ZPL_CONF_WAIT(name)               zpl_conf_wait_##name()
#define ZPL_CONF_WAIT_DECLARE(name)  void zpl_conf_wait_##name(void);

#define ZPL_CONF_IS_ENABLED(name)              zpl_conf_is_enabled_##name()
#define ZPL_CONF_IS_ENABLED_DECLARE(name) bool zpl_conf_is_enabled_##name(void);

#define ZPL_CONF_SET(name, state)          zpl_conf_set_##name(state)
#define ZPL_CONF_SET_DECLARE(name)    void zpl_conf_set_##name(bool state);

#define ZPL_CONF_DECLARE(name, ...)   \
	ZPL_CONF_IS_ENABLED_DECLARE(name) \
	ZPL_CONF_WAIT_DECLARE(name)       \
	ZPL_CONF_SET_DECLARE(name)

CONFIGS(ZPL_CONF_DECLARE)

#define ZPL_CONF_RETURN_IF_DISABLED(name) \
	if (!ZPL_CONF_IS_ENABLED(name)) {     \
		return;                           \
	}

#ifdef __cplusplus
}
#endif

#endif /* ZEPHYR_PROFILING_LIB_CONFIGURATION_H_ */
