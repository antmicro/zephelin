*** Variables ***
${SOCKET_PORT}                      4321

*** Settings ***
Resource			${KEYWORDS}
Resource			../../common/socket.robot
Library				../../common/TraceTester.py

*** Test Cases ***
Should Display Demo Traces
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Wait For Trace On Uart	zpl_inference_enter  cpu_id=${1}  timeout=60
	Wait For Trace On Uart	zpl_inference_enter  cpu_id=${2}  timeout=60
	Wait For Trace On Uart	zpl_inference_enter  cpu_id=${3}  timeout=60

	Wait For Trace On Uart	zpl_tvm_enter        cpu_id=${1}  timeout=60
	Wait For Trace On Uart	zpl_tvm_enter        cpu_id=${2}  timeout=60
	Wait For Trace On Uart	zpl_tvm_enter        cpu_id=${3}  timeout=60

	Wait For Trace On Uart	zpl_tvm_exit         cpu_id=${1}  timeout=60
	Wait For Trace On Uart	zpl_tvm_exit         cpu_id=${2}  timeout=60
	Wait For Trace On Uart	zpl_tvm_exit         cpu_id=${3}  timeout=60

	Wait For Trace On Uart	zpl_inference_exit   cpu_id=${1}  timeout=60
	Wait For Trace On Uart	zpl_inference_exit   cpu_id=${2}  timeout=60
	Wait For Trace On Uart	zpl_inference_exit   cpu_id=${3}  timeout=60

	Trace Tester Close Socket
