/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef ZPL_LIB_H_
#define ZPL_LIB_H_

#include <stdint.h>
#include <zephyr/tracing/tracing.h>

#ifdef __cplusplus
extern "C" {
#endif

struct zpl_code_scope_conf {
	char *conf_name;
	bool is_enabled;
};

int zpl_init(void);
void zpl_code_scope_enter(struct zpl_code_scope_conf scope_conf);
void zpl_code_scope_exit(struct zpl_code_scope_conf scope_conf);
int __zpl_scope_enter_exit(int is_leaving, struct zpl_code_scope_conf scope_conf);

#ifdef CONFIG_ZPL_SCOPE_MARKING
#define ZPL_MARK_CODE_SCOPE(config) for (int __zpl_scope_iterator = 0; \
		__zpl_scope_iterator < __zpl_scope_enter_exit(__zpl_scope_iterator, config); \
		__zpl_scope_iterator++)

#define ZPL_CODE_SCOPE_DEFINE(name, enabled) \
	STRUCT_SECTION_ITERABLE(zpl_code_scope_conf, name) = { \
		.conf_name = (char *) #name, \
		.is_enabled = enabled, \
	}
#else
#define ZPL_MARK_CODE_SCOPE(config) /**/
#define ZPL_CODE_SCOPE_DEFINE(name, enabled) /**/
#endif /* CONFIG_ZPL_SCOPE_MARKING */

#if defined(CONFIG_INSTRUMENTATION) && !defined(CONFIG_ZPL_INTERNALS_INSTRUMENTATION)
#include <zephyr/instrumentation/instrumentation.h>

int __zpl_disable_instr(int __zpl_disable_instr_iter, bool __zpl_instr_enabled);

#define __no_zpl_instrumentation__ __no_instrumentation__

#define ZPL_DISABLE_INSTRUMENTATION \
	for (struct { int i; bool enabled; } __zpl_instr = { 0, instr_enabled() }; \
		__zpl_instr.i < __zpl_disable_instr(__zpl_instr.i, __zpl_instr.enabled); \
		++__zpl_instr.i)
#else
#define __no_zpl_instrumentation__ /**/
#define ZPL_DISABLE_INSTRUMENTATION
#endif

#ifdef CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT
#undef sys_trace_named_event
#define sys_trace_named_event(name, arg0, arg1) zpl_named_event(name, arg0, arg1)
void zpl_named_event(const char *name, uint32_t arg0, uint32_t arg1);
#endif /* CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT */

#ifdef __cplusplus
}
#endif

#endif /* ZPL_LIB_H_ */
