#ifndef ZPL_CPU_LOAD_EVENT_H_
#define ZPL_CPU_LOAD_EVENT_H_

/**
 * CPU load profiling.
 */

#include <stdint.h>

#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
/* CPU load event ID */
#define ZPL_CPU_LOAD_EVENT 0xC0

/**
 * CPU load event structure.
 */
typedef struct __packed {
	uint32_t timestamp;
	uint8_t id;
	uint16_t cpu_load; /* CPU load denoted by a number 0-1000 */
} zpl_cpu_load_event_t;
#endif /* defined(CONFIG_ZPL_TRACE_FORMAT_CTF) */

/**
 * Emits CPU load event.
 */
void zpl_emit_cpu_load_event(void);

#endif /* ZPL_CPU_LOAD_EVENT_H_ */
