#pragma once

extern "C" {
#include <zpl/tflm_events.h>
}
#include <tensorflow/lite/micro/micro_profiler_interface.h>
#include <tensorflow/lite/micro/micro_interpreter.h>
#include <tensorflow/lite/core/c/common.h>
#include <cstdint>

namespace zpl {

/**
 * Profiler that emits events before and after operators execution in TFLite interpreter.
 */
class TFLMProfiler : public tflite::MicroProfilerInterface {
public:
	TFLMProfiler() = default;
	virtual ~TFLMProfiler() = default;
	/**
	 * Method called before op execution. Marks event beginning.
	 *
	 * @param subgraph_idx Index of TFLite interpreter subgraph.
	 * @param subgraph_idx Index of operator in the subgraph.
	 * @param tag Name of the operator.
	 *
	 * @returns Handle of the created event.
	 */
	virtual uint32_t BeginEvent(uint16_t subgraph_idx, uint16_t op_idx, const char *tag) override;
	/**
	 * Method called after op execution. Marks event end.
	 *
	 * @param event_handle Handle of the event that has ended.
	 */
	virtual void EndEvent(uint32_t event_handle) override;
	/**
	 * Dumps events from buffer to trace backend.
	 */
	void DumpEvents();
	/**
	 * Sets MicroInterpreter which will be used to obtain more data.
	 *
	 * @param interpreter Pointer to the selected interpreter.
	 */
	void SetInterpreter(const tflite::MicroInterpreter* interpreter);
	/**
	 * Sets MicroAllocator which will be used to obtain more data.
	 *
	 * @param allocator Pointer to the selected allocator.
	 */
	void SetAllocator(const tflite::MicroAllocator* allocator);

private:
	/* Buffers with events data */
	uint16_t subgraph_idx_[CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS];
	uint16_t op_idx_[CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS];
	const char* tags_[CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS];
	uint32_t begin_cycles_[CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS];
	uint32_t end_cycles_[CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS];
	uint32_t begin_arena_used_bytes_[CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS];
	uint32_t end_arena_used_bytes_[CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS];
	uint32_t begin_arena_tail_usage_[CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS];
	uint32_t end_arena_tail_usage_[CONFIG_ZPL_TFLM_PROFILER_MAX_EVENTS];
	int num_events_ = 0;

	/* Pointer to interpreter that is used to obtain more data */
	const tflite::MicroInterpreter* interpreter_ = nullptr;
	/* Pointer to allocator that is used to obtain more data */
	const tflite::MicroAllocator* allocator_ = nullptr;
};

} /* namespace zpl */
