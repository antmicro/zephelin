*** Settings ***
Resource			${KEYWORDS}

*** Test Cases ***
Should Display OP Trace
	Prepare Machine

	Wait For Line On Uart	zpl_tvm_enter_event: op_idx=3 tag=tvmgen_default_fused_nn_conv2d_add_nn_relu
	Wait For Line On Uart	zpl_tvm_exit_event: op_idx=3 tag=tvmgen_default_fused_nn_conv2d_add_nn_relu
