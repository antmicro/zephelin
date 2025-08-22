/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef ZPL_TVM_PROFILER_H_
#define ZPL_TVM_PROFILER_H_
#include <tvm/runtime/crt/profiler.h>

/**
 * Called by TVMProfiler before op execution. Marks event beginning.
 *
 * @param op_idx Index of the op in TVM graph.
 * @param tag Name of the op in TVM graph.
 *
 * @returns Handle of the created event.
 */
int zpl_tvm_profiler_begin_event(int op_idx, const char *tag);

/**
 * Called by TVMProfiler after op execution. Marks event end.
 *
 * @param event_handle Handle of the event that has ended.
 */
void zpl_tvm_profiler_end_event(int event_handle);

/**
 * Dumps events from buffer to trace backend.
 */
void zpl_tvm_profiler_dump_events(void);

#endif /* ZPL_TVM_PROFILER_H_ */
