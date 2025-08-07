#ifndef ZPL_LIB_H_
#define ZPL_LIB_H_

#include <stdint.h>
#include <zephyr/tracing/tracing.h>

struct zpl_code_scope_conf {
	char* conf_name;
	bool is_enabled;
};

int zpl_init(void);
void zpl_code_scope_enter(struct zpl_code_scope_conf);
void zpl_code_scope_exit(struct zpl_code_scope_conf);
int __zpl_scope_enter_exit(int is_leaving, struct zpl_code_scope_conf);

#define ZPL_MARK_CODE_SCOPE(config) \
	for (int __zpl_scope_iterator = 0; __zpl_scope_iterator < __zpl_scope_enter_exit(__zpl_scope_iterator, config); __zpl_scope_iterator++)

#define ZPL_CODE_SCOPE_DEFINE(name, enabled)                                    \
	STRUCT_SECTION_ITERABLE(zpl_code_scope_conf, name) = {                        \
		.conf_name = #name,															                            \
		.is_enabled = enabled,                                                      \
	}

#ifdef CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT
#undef sys_trace_named_event
#define sys_trace_named_event(name, arg0, arg1) zpl_named_event(name, arg0, arg1)
void zpl_named_event(const char *name, uint32_t arg0, uint32_t arg1);
#endif /* CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT */

#endif /* ZPL_LIB_H_ */
