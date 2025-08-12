*** Variables ***
${SOCKET_PORT}                      4321

*** Settings ***
Resource			${KEYWORDS}
Resource			../../common/socket.robot
Library				../../../tests/TraceTester.py

*** Test Cases ***
Should Display TFLM OP Name
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${0}	tag=CONV_2D	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${0}	tag=CONV_2D	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${1}	tag=MAX_POOL_2D	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${1}	tag=MAX_POOL_2D	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${2}	tag=CONV_2D	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${2}	tag=CONV_2D	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${3}	tag=MAX_POOL_2D	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${3}	tag=MAX_POOL_2D	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${4}	tag=RESHAPE	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${4}	tag=RESHAPE	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${5}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${5}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${6}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${6}	tag=FULLY_CONNECTED	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${7}	tag=SOFTMAX	thread_id=any	arena_used_bytes=any	arena_tail_usage=any
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${7}	tag=SOFTMAX	thread_id=any	arena_used_bytes=any	arena_tail_usage=any

	Trace Tester Close Socket
