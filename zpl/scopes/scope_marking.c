/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zpl.h>
#include <zpl/configuration.h>
#include <zpl/scope_event.h>

int __zpl_scope_enter_exit(int is_leaving, struct zpl_code_scope_conf config) {
	if (is_leaving) {
		zpl_code_scope_exit(config);
	} else {
		zpl_code_scope_enter(config);
	}
	return 1;
}

void zpl_code_scope_enter(struct zpl_code_scope_conf config) {
	if (config.is_enabled) {
		zpl_emit_scope_event(config.conf_name, 0);
	}
}

void zpl_code_scope_exit(struct zpl_code_scope_conf config) {
	if (config.is_enabled) {
		zpl_emit_scope_event(config.conf_name, 1);
	}
}
