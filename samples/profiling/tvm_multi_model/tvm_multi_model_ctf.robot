*** Variables ***
${SOCKET_PORT}                      4321

*** Settings ***
Resource			${KEYWORDS}
Resource			../../common/socket.robot
Library				../../common/TraceTester.py

*** Test Cases ***
Should Display OP Name
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Wait For Trace On Uart	zpl_inference_enter	model_id=any
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${3}	tag=tvmgen_default_fused_nn_conv2d_add_nn_relu
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${3}	tag=tvmgen_default_fused_nn_conv2d_add_nn_relu
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${4}	tag=tvmgen_default_fused_nn_max_pool2d
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${4}	tag=tvmgen_default_fused_nn_max_pool2d
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${7}	tag=tvmgen_default_fused_nn_conv2d_add_nn_relu_1
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${7}	tag=tvmgen_default_fused_nn_conv2d_add_nn_relu_1
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${8}	tag=tvmgen_default_fused_nn_max_pool2d_1
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${8}	tag=tvmgen_default_fused_nn_max_pool2d_1
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${12}	tag=tvmgen_default_fused_nn_dense_add_nn_relu
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${12}	tag=tvmgen_default_fused_nn_dense_add_nn_relu
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${15}	tag=tvmgen_default_fused_nn_dense_add
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${15}	tag=tvmgen_default_fused_nn_dense_add
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${16}	tag=tvmgen_default_fused_nn_softmax
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${16}	tag=tvmgen_default_fused_nn_softmax
	Wait For Trace On Uart	zpl_inference_exit	model_id=any
	Wait For Trace On Uart	zpl_inference_enter	model_id=any
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${6}	tag=tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast	timeout=20
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${6}	tag=tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${11}	tag=tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${11}	tag=tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_1
	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${16}	tag=tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${16}	tag=tvmgen_quantized_fused_nn_dense_subtract_add_fixed_point_multiply_add_clip_cast_2
	Wait For Trace On Uart	zpl_inference_exit	model_id=any

	Trace Tester Close Socket
