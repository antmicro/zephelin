#ifndef ZPL_TFLM_EVENTS_H_
#define ZPL_TFLM_EVENTS_H_

#include <zephyr/kernel.h>
#include <stdint.h>

#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
/* TFLite Micro events IDs */
#define ZPL_TFLM_ENTER_EVENT 0xA0
#define ZPL_TFLM_EXIT_EVENT 0xA1

typedef struct __packed {
	uint32_t timestamp;
	uint8_t id;
	uint32_t thread_id;
	uint16_t subgraph_idx;
	uint16_t op_idx;
	uint16_t tag_len;
	uint8_t tag[CONFIG_ZPL_TRACE_CTF_MAX_STR_LEN];
	uint32_t arena_used_bytes;
	uint32_t arena_tail_usage;
} zpl_tflm_event_t;
#endif /* defined(CONFIG_ZPL_TRACE_FORMAT_CTF) */

void zpl_emit_tflm_enter_event(
	uint32_t cycles, uint16_t subgraph_idx, uint16_t op_idx, const char *tag,
	uint32_t arena_used_bytes, uint32_t arena_tail_usage);

void zpl_emit_tflm_exit_event(
	uint32_t cycles, uint16_t subgraph_idx, uint16_t op_idx, const char *tag,
	uint32_t arena_used_bytes, uint32_t arena_tail_usage);

#endif /* ZPL_TFLM_EVENTS_H_ */
