#include <zpl/tflm_profiler.hpp>

extern "C" {
#include <zpl/tflm_events.h>
#include <zephyr/kernel.h>
}

namespace zpl {

#if defined(CONFIG_ZPL_TRACE_FULL_MODE) || defined(CONFIG_ZPL_TRACE_LAYER_PROFILING_MODE)

uint32_t TFLMProfiler::BeginEvent(uint16_t subgraph_idx, uint16_t op_idx, const char *tag) {
	if (num_events_ >= CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS) {
		return -1;
	}
	int event_handle = num_events_;
	uint32_t arena_used_bytes = -1;
	uint32_t arena_tail_usage = -1;

	subgraph_idx_[event_handle] = subgraph_idx;
	op_idx_[event_handle] = op_idx;
	tags_[event_handle] = tag;

	if (nullptr != allocator_) {
		arena_used_bytes = allocator_->used_bytes();
		arena_tail_usage = allocator_->GetDefaultTailUsage(true);
	} else if (nullptr != interpreter_) {
		arena_used_bytes = interpreter_->arena_used_bytes();
	}

	zpl_emit_tflm_enter_event(
		k_cycle_get_32(),
		subgraph_idx,
		op_idx,
		tag,
		arena_used_bytes,
		arena_tail_usage);

	++num_events_;
	return event_handle;
}

void TFLMProfiler::EndEvent(uint32_t event_handle) {
	if (event_handle >= CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS) {
		return;
	}
	uint32_t arena_used_bytes = -1;
	uint32_t arena_tail_usage = -1;

	arena_used_bytes = -1;
	arena_tail_usage = -1;
	if (nullptr != allocator_) {
		arena_used_bytes = allocator_->used_bytes();
		arena_tail_usage = allocator_->GetDefaultTailUsage(true);
	} else if (nullptr != interpreter_) {
		arena_used_bytes = interpreter_->arena_used_bytes();
	}
	zpl_emit_tflm_exit_event(
		k_cycle_get_32(),
		subgraph_idx_[event_handle],
		op_idx_[event_handle],
		tags_[event_handle],
		arena_used_bytes,
		arena_tail_usage);
}

void TFLMProfiler::DumpEvents() {
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
