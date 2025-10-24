*** Settings ***
Resource			${KEYWORDS}

*** Test Cases ***
Should Display TFLM and TVM Events
	Prepare Machine

	Wait For Line On Uart	zpl_scope_enter \\d+ tflm_init	treatAsRegex=true
	Wait For Line On Uart	zpl_scope_exit \\d+ tflm_init	treatAsRegex=true
	Wait For Line On Uart	zpl_scope_enter \\d+ tflm_model_load	treatAsRegex=true
	Wait For Line On Uart	zpl_scope_exit \\d+ tflm_model_load	treatAsRegex=true
	Wait For Line On Uart	zpl_scope_enter \\d+ tflm_model_load	treatAsRegex=true
	Wait For Line On Uart	zpl_scope_exit \\d+ tflm_model_load	treatAsRegex=true
	Wait For Line On Uart	zpl_scope_enter \\d+ tvm_init	treatAsRegex=true
	Wait For Line On Uart	zpl_scope_exit \\d+ tvm_init	treatAsRegex=true
	Wait For Line On Uart	zpl_scope_enter \\d+ tvm_model_load	treatAsRegex=true
	Wait For Line On Uart	zpl_scope_exit \\d+ tvm_model_load	treatAsRegex=true
	Wait For Line On Uart	zpl_scope_enter \\d+ tvm_model_load	treatAsRegex=true
	Wait For Line On Uart	zpl_scope_exit \\d+ tvm_model_load	treatAsRegex=true
	Wait For Line On Uart	zpl_inference_enter: model_id
	Wait For Line On Uart	zpl_tflm_enter_event: subgraph_idx=0 op_idx=0 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_exit_event: subgraph_idx=0 op_idx=0 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_enter_event: subgraph_idx=0 op_idx=1 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_exit_event: subgraph_idx=0 op_idx=1 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_enter_event: subgraph_idx=0 op_idx=2 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_exit_event: subgraph_idx=0 op_idx=2 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_inference_exit: model_id
	Wait For Line On Uart	zpl_inference_enter: model_id
	Wait For Line On Uart	zpl_tflm_enter_event: subgraph_idx=0 op_idx=0 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_exit_event: subgraph_idx=0 op_idx=0 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_enter_event: subgraph_idx=0 op_idx=1 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_exit_event: subgraph_idx=0 op_idx=1 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_enter_event: subgraph_idx=0 op_idx=2 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_exit_event: subgraph_idx=0 op_idx=2 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_inference_exit: model_id
	Wait For Line On Uart	zpl_inference_enter: model_id
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=6 tag=tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=6 tag=tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=11 tag=tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=11 tag=tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=16 tag=tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=16 tag=tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2
	Wait For Line On Uart	zpl_inference_exit: model_id
	Wait For Line On Uart	zpl_inference_enter: model_id
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=6 tag=tvmgen_sine2_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=6 tag=tvmgen_sine2_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=11 tag=tvmgen_sine2_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=11 tag=tvmgen_sine2_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=16 tag=tvmgen_sine2_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=16 tag=tvmgen_sine2_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2
	Wait For Line On Uart	zpl_inference_exit: model_id
