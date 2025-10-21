/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>

#include <zpl.h>

/* size of stack area used by each thread */
#define STACK_SIZE 1024

/* number of threads to run */
#define THREADS_NUM 4

static K_THREAD_STACK_ARRAY_DEFINE(tstack, THREADS_NUM, STACK_SIZE);
static struct k_thread tthread[THREADS_NUM];
static struct k_sem tsem[THREADS_NUM];

void thread_loop(void *my_sem_, void *other_sem_, void *arg3)
{
	struct k_sem *my_sem = (struct k_sem *)my_sem_;
	struct k_sem *other_sem = (struct k_sem *)other_sem_;
	char my_name[20];

	snprintf(my_name, sizeof(my_name), "%s", k_thread_name_get(k_current_get()));

	while (true) {
		/* take my semaphore */
		k_sem_take(my_sem, K_FOREVER);

		printk("%s: running on cpu %d\n", my_name, arch_curr_cpu()->id);
		sys_trace_named_event(my_name, arch_curr_cpu()->id, 0);

		/* wait a while, then let other thread have a turn */
		k_busy_wait(50);
		k_msleep(10);

		k_sem_give(other_sem);
	}
}

int main(void)
{
	zpl_init();

	/* initialize semaphores */
	for (int i = 0; i < THREADS_NUM; ++i) {
		k_sem_init(&tsem[i], i == 0 ? 1 : 0, 1);
	}

	/* create and start threads */
	for (int i = 0; i < THREADS_NUM; ++i) {
		char thread_name[32];
		snprintf(thread_name, sizeof(thread_name), "thread_%c", 'a' + i);
		k_thread_create(&tthread[i], tstack[i], STACK_SIZE, thread_loop, (void *)&tsem[i],
				(void *)&tsem[(i + 1) % THREADS_NUM], NULL, 7, 0, K_FOREVER);
		k_thread_name_set(&tthread[i], thread_name);
		k_thread_cpu_pin(&tthread[i], i % arch_num_cpus());
		k_thread_start(&tthread[i]);
	}

	return 0;
}
