#include <zpl/tvm_events.h>

#include <zephyr/kernel.h>
#include <zephyr/tracing/tracing_format.h>

#include <stdio.h>

void zpl_emit_tvm_enter_event(uint32_t cycles, uint8_t op_idx, const char* tag)
{
#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
	zpl_tvm_enter_event_t zpl_tvm_enter_event = {
		.timestamp = k_cyc_to_ns_floor64(cycles),
		.op_idx = op_idx,
		.id = ZPL_TVM_BEGIN_EVENT,
		.thread_id = (uint32_t)k_current_get(),
		.tag_len = CONFIG_ZPL_TRACE_CTF_MAX_LONG_STR_LEN,
	};
	snprintf(&(zpl_tvm_enter_event.tag[0]), CONFIG_ZPL_TRACE_CTF_MAX_LONG_STR_LEN, "%s", tag);

	tracing_format_raw_data(
		(uint8_t *)&zpl_tvm_enter_event, sizeof(zpl_tvm_enter_event)
	);
#elif defined(CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT)
	TRACING_STRING("zpl_tvm_enter_event: op_idx=%d tag=%s\n", op_idx, tag);
#endif /* CONFIG_ZPL_TRACE_FORMAT_* */
}

void zpl_emit_tvm_exit_event(uint32_t cycles, uint8_t op_idx, const char* tag)
{
#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
	zpl_tvm_exit_event_t zpl_tvm_exit_event = {
		.timestamp = k_cyc_to_ns_floor64(cycles),
		.op_idx = op_idx,
		.id = ZPL_TVM_END_EVENT,
		.thread_id = (uint32_t)k_current_get(),
		.tag_len = CONFIG_ZPL_TRACE_CTF_MAX_LONG_STR_LEN,
	};
	snprintf(&(zpl_tvm_exit_event.tag[0]), CONFIG_ZPL_TRACE_CTF_MAX_LONG_STR_LEN, "%s", tag);

	tracing_format_raw_data(
		(uint8_t *)&zpl_tvm_exit_event, sizeof(zpl_tvm_exit_event)
	);
#elif defined(CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT)
	TRACING_STRING("zpl_tvm_exit_event: op_idx=%d tag=%s\n", op_idx, tag);
#endif /* CONFIG_ZPL_TRACE_FORMAT_* */
}
