*** Variables ***
${SOCKET_PORT}                      4321

*** Settings ***
Resource			${KEYWORDS}
Resource			../../common/socket.robot
Library				../../common/TraceTester.py

*** Test Cases ***
Should Display TFLM OP Name
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Wait For Trace On Uart	zpl_tflm_enter	subgraph_idx=${0}	op_idx=${0}	tag=TFLM_OP	arena_used_bytes=${0}	arena_tail_usage=${1}	thread_id=any
	Wait For Trace On Uart	zpl_tflm_exit	subgraph_idx=${0}	op_idx=${0}	tag=TFLM_OP	arena_used_bytes=${2}	arena_tail_usage=${3}	thread_id=any

	Trace Tester Close Socket
