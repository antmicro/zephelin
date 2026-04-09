/*
 * Copyright (c) 2026 Analog Devices, Inc.
 * Copyright (c) 2026 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <bench.h>

#include <zephyr/kernel.h>
#include <zephyr/kernel/thread_stack.h>

#include <stdio.h>

#define WORKER_ITERS    10
#define WORKER_COUNT    10
#define WORKER_SEM_INIT 2

K_THREAD_STACK_ARRAY_DEFINE(thread_stacks, WORKER_COUNT, 1024);

int global_counter;

K_MUTEX_DEFINE(global_counter_mutex);

K_SEM_DEFINE(sleep_semaphore, WORKER_SEM_INIT, WORKER_SEM_INIT)

void worker(void *p1, void *p2, void *p3)
{
	int idx = *(int *)p1;

	for (int i = 0; i < WORKER_ITERS; i++) {
		k_sem_take(&sleep_semaphore, K_FOREVER);
		k_msleep((k_uptime_get() * (idx + 1)) % 8);
		k_sem_give(&sleep_semaphore);
		k_mutex_lock(&global_counter_mutex, K_FOREVER);
		global_counter += 1;
		k_mutex_unlock(&global_counter_mutex);
	}
}

void benchmark_setup(void)
{
}

void benchmark_teardown(void)
{
}

void benchmark_run(void)
{
	static k_tid_t thread_handles[WORKER_COUNT];
	static struct k_thread thread_data[WORKER_COUNT];

	for (int i = 0; i < WORKER_COUNT; i++) {
		thread_handles[i] = k_thread_create(
			&thread_data[i], thread_stacks[i], K_THREAD_STACK_SIZEOF(thread_stacks[i]),
			(k_thread_entry_t)worker, &i, NULL, NULL, 0, 0, K_NO_WAIT);
	}

	for (int i = 0; i < WORKER_COUNT; i++) {
		k_thread_join(thread_handles[i], K_FOREVER);
	}
}
