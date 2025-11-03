*** Settings ***
Resource			${KEYWORDS}

*** Test Cases ***
Should Display OP Trace
	Prepare Machine

	Wait For Line On Uart	zpl_inference_enter: model_id
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=3 tag=tvmgen_default_fused_nn_conv2d_add_nn_relu
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=3 tag=tvmgen_default_fused_nn_conv2d_add_nn_relu
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=4 tag=tvmgen_default_fused_nn_max_pool2d
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=4 tag=tvmgen_default_fused_nn_max_pool2d
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=7 tag=tvmgen_default_fused_nn_conv2d_add_nn_relu_1
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=7 tag=tvmgen_default_fused_nn_conv2d_add_nn_relu_1
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=8 tag=tvmgen_default_fused_nn_max_pool2d_1
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=8 tag=tvmgen_default_fused_nn_max_pool2d_1
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=12 tag=tvmgen_default_fused_nn_dense_add_nn_relu
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=12 tag=tvmgen_default_fused_nn_dense_add_nn_relu
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=15 tag=tvmgen_default_fused_nn_dense_add
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=15 tag=tvmgen_default_fused_nn_dense_add
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=16 tag=tvmgen_default_fused_nn_softmax
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=16 tag=tvmgen_default_fused_nn_softmax
	Wait For Line On Uart	zpl_inference_exit: model_id
	Wait For Line On Uart	zpl_inference_enter: model_id
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=2 tag=tvmgen_quantized_fused_reshape_cast_subtract
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=2 tag=tvmgen_quantized_fused_reshape_cast_subtract
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=6 tag=tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=6 tag=tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=7 tag=tvmgen_quantized_fused_reshape_cast_subtract_1
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=7 tag=tvmgen_quantized_fused_reshape_cast_subtract_1
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=10 tag=tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_1
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=10 tag=tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_1
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=11 tag=tvmgen_quantized_fused_reshape_cast_subtract_1
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=11 tag=tvmgen_quantized_fused_reshape_cast_subtract_1
	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=14 tag=tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_2
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=14 tag=tvmgen_quantized_fused_nn_dense_add_fixed_point_multiply_add_clip_cast_2
	Wait For LineOn Uart	zpl_inference_exit: model_id
