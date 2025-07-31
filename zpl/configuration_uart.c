/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/lib.h>
#include <zpl/configuration.h>
#include <zephyr/kernel.h>
#include <zephyr/shell/shell.h>

#define ZPL_WAIT_FOR_CONF_DEF(name, config)                             \
	void zpl_wait_for_##name(void)                                          \
	{                                                                       \
		k_mutex_lock(&zpl_##name_lock, K_FOREVER);                            \
		if (!IS_ENABLED(config) && !zpl_##name_flag) {                        \
			k_condvar_wait(&zpl_##name_condvar, &zpl_##name_lock, K_FOREVER);   \
		}                                                                     \
		k_mutex_unlock(&zpl_##name_lock);                                     \
	}

#define ZPL_CHECK_IF_CONF_DEF(name, config)                             \
	bool zpl_check_if_conf_##name(void)                                     \
	{                                                                       \
		return IS_ENABLED(config) || zpl_##name_flag;                         \
	}

#define ZPL_CONF_VARIABLES(name)         \
	K_MUTEX_DEFINE(zpl_##name_lock);       \
	K_CONDVAR_DEFINE(zpl_##name_condvar);  \
	volatile bool zpl_##name_flag = false;

#define ZPL_CONF_CHANGE_STATE_DEF(name)       \
	void zpl_change_state_##name(bool state)      \
	{                                             \
		k_mutex_lock(&zpl_##name_lock, K_FOREVER);  \
		zpl_##name_flag = state;                    \
		if (zpl_##name_flag) {                      \
			k_condvar_signal(&zpl_##name_condvar);    \
		}                                           \
		k_mutex_unlock(&zpl_##name_lock);           \
	}

#define ZPL_CONF_SHELL_DEF(name)                                             \
	static int enable_##name(const struct shell *sh, size_t argc, char **argv)   \
	{                                                                            \
		zpl_change_state_##name(true);                                             \
		return 0;                                                                  \
	}                                                                            \
	static int disable_##name(const struct shell *sh, size_t argc, char **argv)  \
	{                                                                            \
		zpl_change_state_##name(false);                                            \
		return 0;                                                                  \
	}                                                                            \
	SHELL_STATIC_SUBCMD_SET_CREATE(sub_##name,                                   \
	        SHELL_CMD(enable, NULL, #name" - enable", enable_##name),             \
	        SHELL_CMD(disable, NULL, #name" - disable", disable_##name),           \
	        SHELL_SUBCMD_SET_END                                                 \
	);                                                                           \
	SHELL_CMD_REGISTER(name, &sub_##name, #name, NULL);

#define ZPL_CONF_UART_DEF(name, config)   \
	ZPL_CONF_VARIABLES(name)                \
	ZPL_WAIT_FOR_CONF_DEF(name, config)     \
	ZPL_CHECK_IF_CONF_DEF(name, config)     \
	ZPL_CONF_CHANGE_STATE_DEF(name)         \
	ZPL_CONF_SHELL_DEF(name)

#ifdef CONFIG_ZPL_SCOPE_MARKING

void zpl_change_state_dynamic_conf(char* conf_name, bool state) {
	STRUCT_SECTION_FOREACH(zpl_code_scope_conf, config) {
		if (strcmp(config->conf_name, conf_name) == 0) {
			config->is_enabled = state;
		}
	}
}

static int zpl_enable_dynamic_conf(const struct shell *sh, size_t argc, char **argv)
{
	if (argc < 2) {
		shell_error(sh, "Usage: dynamic_conf enable <config_name>");
		return 1;
	}
	zpl_change_state_dynamic_conf(argv[1], true);
	return 0;
}

static int zpl_disable_dynamic_conf(const struct shell *sh, size_t argc, char **argv)
{
	if (argc < 2) {
		shell_error(sh, "Usage: dynamic_conf disable <config_name>");
		return 1;
	}
	zpl_change_state_dynamic_conf(argv[1], false);
	return 0;
}

static int zpl_list_dynamic_conf(const struct shell *sh, size_t argc, char **argv)
{
	shell_print(sh, "Available configs:");
	STRUCT_SECTION_FOREACH(zpl_code_scope_conf, config) {
		shell_print(sh, "\t%s:\t%s", config->conf_name, config->is_enabled ? "enabled" : "disabled");
	}
	return 0;
}

SHELL_STATIC_SUBCMD_SET_CREATE(sub_dynamic_conf,
        SHELL_CMD(enable, NULL, "Dynamic conf - enable", zpl_enable_dynamic_conf),
        SHELL_CMD(disable, NULL, "Dynamic conf - disable", zpl_disable_dynamic_conf),
        SHELL_CMD(list, NULL, "List available dynamic configurations", zpl_list_dynamic_conf),
        SHELL_SUBCMD_SET_END
);
SHELL_CMD_REGISTER(dynamic_conf, &sub_dynamic_conf, "dynamic_conf", NULL);

#endif /* CONFIG_ZPL_SCOPE_MARKING */

/* Config definitions */
ZPL_CONF_UART_DEF(mem_usage_trace, CONFIG_ZPL_MEMORY_USAGE_TRACE)
