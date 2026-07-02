/*
 * Copyright (c) 2025-2026 Analog Devices, Inc.
 * Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zpl/configuration.h>
#include <zpl/tflm_profiler.hpp>
#include <zephyr/logging/log.h>

extern "C" {
#include <zpl.h>
#include <zpl/tflm_event.h>
#include <zpl/time.h>
#include <zephyr/kernel.h>
}

namespace zpl {

#if defined(CONFIG_ZPL_TRACE_FULL_MODE) || defined(CONFIG_ZPL_TRACE_LAYER_PROFILING_MODE)

LOG_MODULE_REGISTER(tflm_profiler, CONFIG_ZPL_LOG_LEVEL);

uint32_t TFLMProfiler::BeginEvent(uint16_t subgraph_idx, uint16_t op_idx, const char *tag) {
	if (num_events_ >= CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS) {
		LOG_WRN_ONCE(
		  "The number of TFLM events exceeded the maximum value (%d), "
		  "resulting trace may be incompleate, please consider "
		  "increasing CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS",
		  CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS);
		return -1;
	}
	int event_handle = num_events_;

	ZPL_DISABLE_INSTRUMENTATION {
		subgraph_idx_[event_handle] = subgraph_idx;
		op_idx_[event_handle] = op_idx;
		tags_[event_handle] = tag;

		int32_t current_arena_used = -1;
		int32_t current_arena_tail = -1;

		if (nullptr != allocator_) {
			current_arena_used = allocator_->used_bytes();
			current_arena_tail = allocator_->GetDefaultTailUsage(true);
		} else if (nullptr != interpreter_) {
			current_arena_used = interpreter_->arena_used_bytes();
		}

		begin_arena_used_bytes_[event_handle] = current_arena_used;
		begin_arena_tail_usage_[event_handle] = current_arena_tail;
#ifdef CONFIG_ZPL_TFLM_PROFILER_DELAYED_EMISSION
		begin_cycles_[event_handle] = zpl_cycles_get();
#else
		zpl_emit_tflm_enter_event(
			zpl_cycles_get(),
			subgraph_idx,
			op_idx,
			tag,
			current_arena_used,
			current_arena_tail
		);
#endif
	}

	++num_events_;
	return event_handle;
}

void TFLMProfiler::EndEvent(uint32_t event_handle) {
	if (event_handle >= CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS) {
		return;
	}

	ZPL_DISABLE_INSTRUMENTATION {
		int32_t current_arena_used = -1;
		int32_t current_arena_tail = -1;

		if (nullptr != allocator_) {
			current_arena_used = allocator_->used_bytes();
			current_arena_tail = allocator_->GetDefaultTailUsage(true);
		} else if (nullptr != interpreter_) {
			current_arena_used = interpreter_->arena_used_bytes();
		}
#ifdef CONFIG_ZPL_TFLM_PROFILER_DELAYED_EMISSION
		end_cycles_[event_handle] = zpl_cycles_get();
		end_arena_used_bytes_[event_handle] = current_arena_used;
		end_arena_tail_usage_[event_handle] = current_arena_tail;
#else
		zpl_emit_tflm_exit_event(
			zpl_cycles_get(),
			subgraph_idx_[event_handle],
			op_idx_[event_handle],
			tags_[event_handle],
			current_arena_used,
			current_arena_tail
		);
#endif
	}
}

void TFLMProfiler::DumpEvents() {
	ZPL_CONF_RETURN_IF_DISABLED(tflm_profiler);
#ifdef CONFIG_ZPL_TFLM_PROFILER_DELAYED_EMISSION
	for (int i = 0; i < num_events_; ++i) {
		zpl_emit_tflm_enter_event(
			begin_cycles_[i],
			subgraph_idx_[i],
			op_idx_[i],
			tags_[i],
			begin_arena_used_bytes_[i],
			begin_arena_tail_usage_[i]);
		zpl_emit_tflm_exit_event(
			end_cycles_[i],
			subgraph_idx_[i],
			op_idx_[i],
			tags_[i],
			end_arena_used_bytes_[i],
			end_arena_tail_usage_[i]);
	}

#endif

	num_events_ = 0;
}

#else /* defined(CONFIG_ZPL_TRACE_FULL_MODE) || defined(CONFIG_ZPL_TRACE_LAYER_PROFILING_MODE) */

uint32_t TFLMProfiler::BeginEvent(uint16_t subgraph_idx, uint16_t op_idx, const char *tag) { return -1; }

void TFLMProfiler::EndEvent(uint32_t event_handle) {}

void TFLMProfiler::DumpEvents() {}

#endif /* defined(CONFIG_ZPL_TRACE_FULL_MODE) || defined(CONFIG_ZPL_TRACE_LAYER_PROFILING_MODE) */

void TFLMProfiler::SetInterpreter(const tflite::MicroInterpreter* interpreter) {
	interpreter_ = interpreter;
}

void TFLMProfiler::SetAllocator(const tflite::MicroAllocator* allocator) {
	allocator_ = allocator;
}

} /* namespace zpl */
