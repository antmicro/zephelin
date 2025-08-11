/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/logging/log.h>
#include <zpl/tvm_event.h>
#include <zpl/tvm_profiler.h>

#include <dlpack/dlpack.h>
#include <tvm/runtime/crt/profiler.h>
#include <tvm/runtime/crt/platform.h>


int zpl_tvm_profiler_create(TVMProfiler **profiler)
{
	DLDevice dev = {kDLCPU, 0};
	ZPL_TVMProfilerState *state;

	int status = 0;

	status = TVMPlatformMemoryAllocate(sizeof(ZPL_TVMProfilerState), dev, (void **)(&state));
	if (status) {
		return status;
	}

	status = TVMPlatformMemoryAllocate(sizeof(TVMProfiler), dev, (void **)(profiler));
	if (status) {
		return status;
	}

	memset(state, 0, sizeof(ZPL_TVMProfilerState));
	(**profiler) = (TVMProfiler){
		.begin_event_cb = zpl_tvm_profiler_begin_event,
		.end_event_cb = zpl_tvm_profiler_end_event,
		.dump_events_cb = zpl_tvm_profiler_dump_events,
		.state = state,
	};

	return 0;
}

int zpl_tvm_profiler_release(TVMProfiler *profiler)
{
	int status = 0;
	DLDevice dev = {kDLCPU, 0};

	status = TVMPlatformMemoryFree(profiler->state, dev);
	if (status) {
		return status;
	}

	return TVMPlatformMemoryFree(profiler, dev);
}

#if defined(CONFIG_ZPL_TRACE_FULL_MODE) || defined(CONFIG_ZPL_TRACE_LAYER_PROFILING_MODE)

LOG_MODULE_REGISTER(tvm_profiler, CONFIG_ZPL_LOG_LEVEL);

int zpl_tvm_profiler_begin_event(void *state, int op_idx, const char *tag)
{
	ZPL_TVMProfilerState *zpl_state = (ZPL_TVMProfilerState *)(state);

	if (zpl_state->num_events_ >= CONFIG_ZPL_TVM_PROFILER_MAX_EVENTS) {
		LOG_WRN_ONCE(
		  "The number of TVM events exceeded the maximum value (%d), "
		  "resulting trace may be incompleate, please consider "
		  "increasing CONFIG_ZPL_TVM_PROFILER_MAX_EVENTS",
		  CONFIG_ZPL_TVM_PROFILER_MAX_EVENTS);
		return -1;
	}
	int event_handle = zpl_state->num_events_;

	zpl_state->begin_cycles_[event_handle] = soft_cycle_get_64();
	zpl_state->op_idx_[event_handle] = op_idx;
	zpl_state->tags_[event_handle] = tag;

	++(zpl_state->num_events_);

	return event_handle;
}

void zpl_tvm_profiler_end_event(void *state, int event_handle)
{
	if (event_handle >= CONFIG_ZPL_TVM_PROFILER_MAX_EVENTS) {
		return;
	}

	ZPL_TVMProfilerState *zpl_state = (ZPL_TVMProfilerState *)(state);

	zpl_state->end_cycles_[event_handle] = soft_cycle_get_64();
}

void zpl_tvm_profiler_dump_events(void *state)
{
	ZPL_TVMProfilerState *zpl_state = (ZPL_TVMProfilerState *)(state);

	for (int i = 0; i < num_events_; ++i) {
		zpl_emit_tvm_enter_event(
			zpl_state->begin_cycles_[i],
			zpl_state->op_idx_[i],
			zpl_state->tags_[i]);
		zpl_emit_tvm_exit_event(
			zpl_state->end_cycles_[i],
			zpl_state->op_idx_[i],
			zpl_state->tags_[i]);
	}

	zpl_state->num_events_ = 0;
}

#else /* defined(CONFIG_ZPL_TRACE_FULL_MODE) || defined(CONFIG_ZPL_TRACE_LAYER_PROFILING_MODE) */

int zpl_tvm_profiler_begin_event(void *state, int op_idx, const char *tag) { return -1; }

void zpl_tvm_profiler_end_event(void *state, int event_handle) {}

void zpl_tvm_profiler_dump_events(void *state) {}

#endif /* defined(CONFIG_ZPL_TRACE_FULL_MODE) || defined(CONFIG_ZPL_TRACE_LAYER_PROFILING_MODE) */
