*** Variables ***
${SOCKET_PORT}                      4321

*** Settings ***
Resource			${KEYWORDS}
Resource			../../common/socket.robot
Library				../../common/TraceTester.py

*** Test Cases ***
Should Display Minimal Traces
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Wait For Trace On Uart	zpl_inference_enter
	Wait For Trace On Uart	zpl_inference_exit

	Wait For Trace On Uart	zpl_memory

	Trace Tester Close Socket

Should Not Display Layer Profiling Traces
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Trace Should Not Be On Uart	zpl_tflm_enter
	Trace Should Not Be On Uart	zpl_tflm_exit

	Trace Tester Close Socket

Should Not Display Full Traces
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Trace Should Not Be On Uart	thread_info

	Trace Tester Close Socket
