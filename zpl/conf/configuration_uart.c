/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl.h>
#include <zpl/configuration.h>
#include <zephyr/shell/shell.h>


#define ZPL_CONF_SHELL_DEFINE(name, ...)                                        \
	static int enable_##name(const struct shell *sh, size_t argc, char **argv)  \
	{                                                                           \
		ZPL_CONF_SET(name, true);                                               \
		return 0;                                                               \
	}                                                                           \
	static int disable_##name(const struct shell *sh, size_t argc, char **argv) \
	{                                                                           \
		ZPL_CONF_SET(name, false);                                              \
		return 0;                                                               \
	}                                                                           \
	SHELL_STATIC_SUBCMD_SET_CREATE(sub_##name,                                  \
		SHELL_CMD(enable, NULL, #name" - enable", enable_##name),               \
		SHELL_CMD(disable, NULL, #name" - disable", disable_##name),            \
		SHELL_SUBCMD_SET_END                                                    \
	);                                                                          \
	SHELL_CMD_REGISTER(name, &sub_##name, #name, NULL);

CONFIGS(ZPL_CONF_SHELL_DEFINE)

#ifdef CONFIG_ZPL_SCOPE_MARKING

void zpl_change_state_dynamic_conf(char *conf_name, bool state)
{
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
		shell_print(sh, "\t%s:\t%s", config->conf_name,
				config->is_enabled ? "enabled" : "disabled");
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
