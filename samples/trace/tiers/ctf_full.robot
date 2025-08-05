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

	Wait For Trace On Uart	thread_info  timeout=30

	Wait For Trace On Uart	zpl_inference_enter  timeout=30

	Wait For Trace On Uart	zpl_tflm_enter  timeout=30
	Wait For Trace On Uart	zpl_tflm_exit  timeout=30

	Wait For Trace On Uart	zpl_inference_exit  timeout=30

	Wait For Trace On Uart	zpl_memory  timeout=30

	Trace Tester Close Socket
