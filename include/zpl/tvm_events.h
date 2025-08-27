#ifndef ZPL_TVM_EVENTS_H_
#define ZPL_TVM_EVENTS_H_

#include <zephyr/kernel.h>
#include <stdint.h>

#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
/* TFLite Micro events IDs */
#define ZPL_TVM_BEGIN_EVENT 0xB0
#define ZPL_TVM_END_EVENT 0xB1

typedef struct __packed {
	uint32_t timestamp;
	uint8_t id;
	uint8_t op_idx;
	uint8_t tag[CONFIG_ZPL_TRACE_CTF_MAX_LONG_STR_LEN];
} zpl_tvm_begin_event_t;

typedef struct __packed {
	uint32_t timestamp;
	uint8_t id;
	uint8_t op_idx;
	uint8_t tag[CONFIG_ZPL_TRACE_CTF_MAX_LONG_STR_LEN];
} zpl_tvm_end_event_t;
#endif /* defined(CONFIG_ZPL_TRACE_FORMAT_CTF) */

void zpl_emit_tvm_begin_event(uint32_t cycles, uint8_t op_idx, const char* tag);

void zpl_emit_tvm_end_event(uint32_t cycles, uint8_t op_idx, const char* tag);

#endif /* ZPL_TVM_EVENTS_H_ */
