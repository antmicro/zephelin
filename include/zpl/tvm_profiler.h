/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef ZPL_TVM_PROFILER_H_
#define ZPL_TVM_PROFILER_H_
#include <tvm/runtime/crt/profiler.h>

#ifdef __cplusplus
extern "C" {
#endif

#if defined(CONFIG_ZPL_TVM_PROFILER)
#include <stdint.h>

typedef struct {
	int num_events_;
	uint8_t op_idx_[CONFIG_ZPL_TVM_PROFILER_MAX_EVENTS];
	uint64_t begin_cycles_[CONFIG_ZPL_TVM_PROFILER_MAX_EVENTS];
	uint64_t end_cycles_[CONFIG_ZPL_TVM_PROFILER_MAX_EVENTS];
	const char *tags_[CONFIG_ZPL_TVM_PROFILER_MAX_EVENTS];
} ZPL_TVMProfilerState;
#endif /* defined(CONFIG_ZPL_TVM_PROFILER) */

/**
 * Called by TVMGraphExecutor_Create. Initializes default profiler.
 *
 * @param profiler Profiler pointer to initialize.
 *
 * @returns Allocation status.
 */
int zpl_tvm_profiler_create(TVMProfiler **);

/**
 * Called by TVMGraphExecutor_Release. Deallocates profiler.
 *
 * @param profiler Profiler to release.
 *
 * @returns Deallocation status.
 */
int zpl_tvm_profiler_release(TVMProfiler *profiler);

/**
 * Called by TVMProfiler before op execution. Marks event beginning.
 *
 * @param op_idx Index of the op in TVM graph.
 * @param tag Name of the op in TVM graph.
 *
 * @returns Handle of the created event.
 */
int zpl_tvm_profiler_begin_event(void *state, int op_idx, const char *tag);

/**
 * Called by TVMProfiler after op execution. Marks event end.
 *
 * @param event_handle Handle of the event that has ended.
 */
void zpl_tvm_profiler_end_event(void *state, int event_handle);

/**
 * Dumps events from buffer to trace backend.
 */
void zpl_tvm_profiler_dump_events(void *state);

#ifdef __cplusplus
}
#endif

#endif /* ZPL_TVM_PROFILER_H_ */
