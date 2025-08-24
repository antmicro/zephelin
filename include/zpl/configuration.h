/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef ZEPHYR_PROFILING_LIB_CONFIGURATION_H_
#define ZEPHYR_PROFILING_LIB_CONFIGURATION_H_

#include <stdbool.h>

#define ZPL_WAIT_FOR_CONF_DEC(name)  void zpl_wait_for_##name(void);
#define ZPL_WAIT_FOR_CONF(name)      zpl_wait_for_##name()

#define ZPL_CHECK_IF_CONF_DEC(name)  bool zpl_check_if_conf_##name(void);
#define ZPL_CHECK_IF_CONF(name)      zpl_check_if_conf_##name()

ZPL_WAIT_FOR_CONF_DEC(mem_usage_trace)
ZPL_CHECK_IF_CONF_DEC(mem_usage_trace)

#endif /* ZEPHYR_PROFILING_LIB_CONFIGURATION_H_ */
