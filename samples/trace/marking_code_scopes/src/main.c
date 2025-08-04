/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zpl/lib.h>

ZPL_CODE_SCOPE_DEFINE(code_scope1, false);
ZPL_CODE_SCOPE_DEFINE(code_scope2, false);
ZPL_CODE_SCOPE_DEFINE(code_scope3, true);
ZPL_CODE_SCOPE_DEFINE(code_scope4, true);

void test_function(int counter)
{
	sys_trace_named_event("test_function", 1, 1);
	ZPL_MARK_CODE_SCOPE(code_scope1) {
		sys_trace_named_event("test_function", 1, 2);
		k_sleep(K_MSEC(100));
	}
}

void test_function2(int counter)
{
	zpl_code_scope_enter(code_scope2);

		sys_trace_named_event("test_function", 2, 1);
		k_sleep(K_MSEC(100));

	zpl_code_scope_exit(code_scope2);
}

void test_recurrent(int counter)
{
	sys_trace_named_event("recurrent_test_function", 1, 1);
	ZPL_MARK_CODE_SCOPE(code_scope4) {
		k_sleep(K_MSEC(100));
		if (counter == 0) return;
		test_recurrent(counter - 1);
	}
}

int main(void)
{
	zpl_init();
	k_sleep(K_MSEC(1000));
	for (int i = 0; i < 10; i++) {
		ZPL_MARK_CODE_SCOPE(code_scope3) {
			test_function(i);
		}
		k_sleep(K_MSEC(100));
	}

	for (int i = 0; i < 5; i++) {
		test_function2(i);
		k_sleep(K_MSEC(100));
	}

	test_recurrent(5);

	return 0;
}
