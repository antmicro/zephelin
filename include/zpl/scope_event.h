#ifndef ZPL_SCOPE_EVENT_H_
#define ZPL_SCOPE_EVENT_H_

#include <stdint.h>

#define ZPL_SCOPE_EVENT 0xEF
#define ZPL_MAX_SCOPE_NAME_LENGTH 30

typedef struct __packed {
	uint32_t timestamp;
	uint8_t id;
	uint8_t scope_name[ZPL_MAX_SCOPE_NAME_LENGTH + 1];
	uint8_t is_exit;
	uint32_t cycles;
	uint32_t for_thread_id;
} zpl_scope_event_t;

void zpl_emit_scope_event(char* scope_name, uint8_t is_exit);

#endif  // ZPL_SCOPE_EVENT_H_
