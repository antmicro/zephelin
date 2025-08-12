*** Variables ***
${SOCKET_PORT}                      4321

*** Settings ***
Resource			${KEYWORDS}
Resource			../../common/socket.robot
Library				../../../tests/TraceTester.py

*** Test Cases ***
Should Display OP Name
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Wait For Trace On Uart	zpl_tvm_enter	op_idx=${3}	tag=tvmgen_default_fused_nn_conv2d_add_nn_relu	thread_id=any
	Wait For Trace On Uart	zpl_tvm_exit	op_idx=${3}	tag=tvmgen_default_fused_nn_conv2d_add_nn_relu	thread_id=any

	Trace Tester Close Socket
