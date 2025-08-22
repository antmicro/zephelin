/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/tvm_event.h>
#include <zpl/tvm_profiler.h>

#include <tvm/runtime/crt/profiler.h>

TVMProfiler tvm_profiler = {
	.begin_event_cb = zpl_tvm_profiler_begin_event,
	.end_event_cb = zpl_tvm_profiler_end_event,
};

#if defined(CONFIG_ZPL_TRACE_FULL_MODE) || defined(CONFIG_ZPL_TRACE_LAYER_PROFILING_MODE)

static int num_events_;
static uint8_t op_idx_[CONFIG_ZPL_TVM_PROFILER_MAX_EVENTS];
static const char *tags_[CONFIG_ZPL_TVM_PROFILER_MAX_EVENTS];


int zpl_tvm_profiler_begin_event(int op_idx, const char *tag)
{
	if (num_events_ >= CONFIG_ZPL_TVM_PROFILER_MAX_EVENTS) {
		return -1;
	}
	int event_handle = num_events_;

	op_idx_[event_handle] = op_idx;
	tags_[event_handle] = tag;

	zpl_emit_tvm_enter_event(
		k_cycle_get_32(),
		op_idx,
		tag);

	++num_events_;

	return event_handle;
}

void zpl_tvm_profiler_end_event(int event_handle)
{
	if (event_handle >= CONFIG_ZPL_TVM_PROFILER_MAX_EVENTS) {
		return;
	}

	zpl_emit_tvm_exit_event(
		k_cycle_get_32(),
		op_idx_[event_handle],
		tags_[event_handle]);
}

void zpl_tvm_profiler_dump_events(void)
{
	num_events_ = 0;
}

#else /* defined(CONFIG_ZPL_TRACE_FULL_MODE) || defined(CONFIG_ZPL_TRACE_LAYER_PROFILING_MODE) */

int zpl_tvm_profiler_begin_event(int op_idx, const char *tag) { return -1; }

void zpl_tvm_profiler_end_event(int event_handle) {}

void zpl_tvm_profiler_dump_events(void) {}

#endif /* defined(CONFIG_ZPL_TRACE_FULL_MODE) || defined(CONFIG_ZPL_TRACE_LAYER_PROFILING_MODE) */
