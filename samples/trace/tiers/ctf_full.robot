*** Variables ***
${SOCKET_PORT}                      4321

*** Settings ***
Resource			${KEYWORDS}
Library				../../../tests/TraceTester.py

*** Keywords ***
Set Up Socket Terminal
	Execute Command		emulation CreateServerSocketTerminal ${SOCKET_PORT} "term" False
	Execute Command		connector Connect ${UART} "term"

*** Test Cases ***
Should Display Full Traces
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Wait For Trace On Uart	thread_info

	Wait For Trace On Uart	zpl_inference_enter
	Wait For Trace On Uart	zpl_inference_exit

	Wait For Trace On Uart	zpl_tflm_enter
	Wait For Trace On Uart	zpl_tflm_exit

	Wait For Trace On Uart	zpl_memory

	Trace Tester Close Socket
