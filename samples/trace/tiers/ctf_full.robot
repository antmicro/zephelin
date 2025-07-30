*** Variables ***
${SOCKET_PORT}                      4321

*** Settings ***
Resource			${KEYWORDS}
Resource			../common/socket.robot
Library				../../../tests/TraceTester.py

*** Test Cases ***
Should Display Full Traces
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Wait For Trace On Uart	thread_info

	Wait For Trace On Uart	zpl_inference_enter

	Wait For Trace On Uart	zpl_tflm_enter
	Wait For Trace On Uart	zpl_tflm_exit

	Wait For Trace On Uart	zpl_inference_exit

	Wait For Trace On Uart	zpl_memory

	Trace Tester Close Socket
