*** Variables ***
${SOCKET_PORT}                      4321

*** Settings ***
Resource			${KEYWORDS}
Resource			../../common/socket.robot
Library				../../common/TraceTester.py

*** Test Cases ***
Should Display TFLM and TVM OP Name
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Wait For Trace On Uart  zpl_scope_enter  scope_name=tflm_init  cycles=any  thread_id=any
	Wait For Trace On Uart  zpl_scope_exit   scope_name=tflm_init  cycles=any  thread_id=any
	Wait For Trace On Uart  zpl_scope_enter  scope_name=tflm_model_load  cycles=any  thread_id=any
	Wait For Trace On Uart  zpl_scope_exit   scope_name=tflm_model_load  cycles=any  thread_id=any
	Wait For Trace On Uart  zpl_scope_enter  scope_name=tflm_model_load  cycles=any  thread_id=any
	Wait For Trace On Uart  zpl_scope_exit   scope_name=tflm_model_load  cycles=any  thread_id=any
	Wait For Trace On Uart  zpl_scope_enter  scope_name=tvm_init  cycles=any  thread_id=any
	Wait For Trace On Uart  zpl_scope_exit   scope_name=tvm_init  cycles=any  thread_id=any
	Wait For Trace On Uart  zpl_scope_enter  scope_name=tvm_model_load  cycles=any  thread_id=any
	Wait For Trace On Uart  zpl_scope_exit   scope_name=tvm_model_load  cycles=any  thread_id=any
	Wait For Trace On Uart  zpl_scope_enter  scope_name=tvm_model_load  cycles=any  thread_id=any
	Wait For Trace On Uart  zpl_scope_exit   scope_name=tvm_model_load  cycles=any  thread_id=any
	Wait For Trace On Uart	zpl_inference_enter	model_id=any
	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${0}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any	timeout=120
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${0}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${1}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${1}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${2}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${2}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_inference_exit	model_id=any
	Wait For Trace On Uart	zpl_inference_enter	model_id=any
	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${0}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any	timeout=120
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${0}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${1}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${1}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${2}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${2}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_inference_exit	model_id=any
	Wait For Trace On Uart	zpl_inference_enter	model_id=any
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${2}	tag=tvmgen_quantized_fused_reshape_cast_subtract	timeout=120
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${2}	tag=tvmgen_quantized_fused_reshape_cast_subtract
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${6}	tag=tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${6}	tag=tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${7}	tag=tvmgen_quantized_fused_reshape_cast_subtract_1
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${7}	tag=tvmgen_quantized_fused_reshape_cast_subtract_1
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${10}	tag=tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_1
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${10}	tag=tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_1
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${11}	tag=tvmgen_quantized_fused_reshape_cast_subtract_1
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${11}	tag=tvmgen_quantized_fused_reshape_cast_subtract_1
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${14}	tag=tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_2
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${14}	tag=tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_2
	Wait For Trace On Uart	zpl_inference_exit	model_id=any
	Wait For Trace On Uart	zpl_inference_enter	model_id=any
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${2}	tag=tvmgen_sine2_fused_reshape_cast_subtract	timeout=120
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${2}	tag=tvmgen_sine2_fused_reshape_cast_subtract
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${6}	tag=tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${6}	tag=tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${7}	tag=tvmgen_sine2_fused_reshape_cast_subtract_1
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${7}	tag=tvmgen_sine2_fused_reshape_cast_subtract_1
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${10}	tag=tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_1
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${10}	tag=tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_1
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${11}	tag=tvmgen_sine2_fused_reshape_cast_subtract_1
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${11}	tag=tvmgen_sine2_fused_reshape_cast_subtract_1
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${14}	tag=tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_2
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${14}	tag=tvmgen_sine2_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_2
	Wait For Trace On Uart	zpl_inference_exit	model_id=any

	Trace Tester Close Socket
