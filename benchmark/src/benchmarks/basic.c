/*
 * Copyright (c) 2026 Analog Devices, Inc.
 * Copyright (c) 2026 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#include <bench.h>

#include <zephyr/sys/util.h>
#include <zpl.h>

ZPL_CODE_SCOPE_DEFINE(mul, true);

#define BENCH_ATTRS __attribute__((optimize("O0"), noinline))


void benchmark_setup(void)
{
}

void benchmark_teardown(void)
{
}

int BENCH_ATTRS basic_add(int a, int b)
{
	return a + b;
}

int BENCH_ATTRS basic_mul(int a, int b)
{
	int acc = 0;
	ZPL_MARK_CODE_SCOPE(mul)
	{
		for (int i = 0; i < b; i++) {
			basic_add(acc, a);
		}
	}
	return acc;
}
int BENCH_ATTRS basic_dot(int a[], int b[], int n)
{
	int acc = 0;

	for (int i = 0; i < n; i++) {
		basic_add(acc, basic_mul(a[i], b[i]));
	}
	return acc;
}

int basic_res;

void benchmark_run(void)
{
	int arr1[] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
	int arr2[] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

	basic_res = basic_dot(arr1, arr2, ARRAY_SIZE(arr1));
}
