/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/usb_backend.h>

#include <zephyr/init.h>
#include <zephyr/tracing/tracing.h>
#include <zephyr/tracing/tracing_format.h>
#include <zephyr/usb/usbd.h>

LOG_MODULE_REGISTER(zpl, CONFIG_ZPL_LOG_LEVEL);

#ifdef CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT
void zpl_named_event(const char *name, uint32_t arg0, uint32_t arg1)
{
	TRACING_STRING("%s: %s (%d; %d)\n", __func__, name, arg0, arg1);
}
#endif /* CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT */

int zpl_init(void)
{
#if defined(CONFIG_ZPL_TRACE_BACKEND_USB)
	struct usbd_context *zpl_usbd = zpl_usbd_init_device();

	if (zpl_usbd == NULL) {
		LOG_ERR("Failed to initialize USB device");
		return 1;
	}

	if (usbd_enable(zpl_usbd)) {
		LOG_ERR("USB backend enable failed");
		return 1;
	}

#endif /* CONFIG_ZPL_TRACE_BACKEND_USB */

	/* Emit event with current thread information, this allows to associate
	 * ID with the main thread
	 */
	sys_port_trace_k_thread_info(k_current_get());
	return 0;
}

#if defined(CONFIG_ZPL_TRACE_BACKEND_UART) && defined(CONFIG_ZPL_TRACE_FORMAT_CTF) && \
	!defined(CONFIG_TRACING_HANDLE_HOST_CMD)

int zpl_ctf_start_tag_emit(void)
{
	tracing_format_raw_data("_zpl_ctf_start__", 16);
	return 0;
}

SYS_INIT(zpl_ctf_start_tag_emit, APPLICATION, 0);

#endif /* defined(CONFIG_ZPL_TRACE_BACKEND_UART) && defined(CONFIG_ZPL_TRACE_FORMAT_CTF) &&
	* !defined(CONFIG_TRACING_HANDLE_HOST_CMD)
	*/

#if defined(CONFIG_ZPL) && defined(CONFIG_ZPL_AUTORUN_INIT) && defined(CONFIG_ZPL_INIT_PRIO)

#if defined(CONFIG_ZPL_INIT_LVL_EARLY)
SYS_INIT(zpl_init, EARLY, CONFIG_ZPL_INIT_PRIO);

#elif defined(CONFIG_ZPL_INIT_LVL_PRE_KERNEL_1)
SYS_INIT(zpl_init, PRE_KERNEL_1, CONFIG_ZPL_INIT_PRIO);

#elif defined(CONFIG_ZPL_INIT_LVL_PRE_KERNEL_2)
SYS_INIT(zpl_init, PRE_KERNEL_2, CONFIG_ZPL_INIT_PRIO);

#elif defined(CONFIG_ZPL_INIT_LVL_POST_KERNEL)
SYS_INIT(zpl_init, POST_KERNEL, CONFIG_ZPL_INIT_PRIO);

#elif defined(CONFIG_ZPL_INIT_LVL_APPLICATION)
SYS_INIT(zpl_init, APPLICATION, CONFIG_ZPL_INIT_PRIO);

#elif defined(CONFIG_ZPL_INIT_LVL_SMP)
SYS_INIT(zpl_init, SMP, CONFIG_ZPL_INIT_PRIO);
#endif

#endif /* defined(CONFIG_ZPL) && defined(CONFIG_ZPL_AUTORUN_INIT) &&
	* defined(CONFIG_ZPL_INIT_PRIO)
	*/

#ifdef CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT
void sys_trace_k_heap_sys_k_aligned_alloc_enter(struct k_heap *h, size_t align,
		size_t size)
{ }
void sys_trace_k_heap_sys_k_aligned_alloc_exit(struct k_heap *h, size_t align, size_t size,
		void *ret)
{ }
void sys_trace_k_heap_sys_k_malloc_enter(struct k_heap *h, size_t size) { }
void sys_trace_k_heap_sys_k_malloc_exit(struct k_heap *h, size_t size, void *ret) { }
void sys_trace_k_thread_foreach_enter(k_thread_user_cb_t user_cb, void *user_data) { }
void sys_trace_k_thread_foreach_exit(k_thread_user_cb_t user_cb, void *user_data) { }
#endif /* CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT */
