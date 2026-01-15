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

	Wait For Trace On Uart	named_event  name=thread_a  arg0=${0}  timeout=90
	Wait For Trace On Uart	named_event  name=thread_b  arg0=${1}  timeout=60
	Wait For Trace On Uart	named_event  name=thread_c  arg0=${2}  timeout=60
	Wait For Trace On Uart	named_event  name=thread_d  arg0=${3}  timeout=60

	Wait For Trace On Uart	named_event  name=thread_a  arg0=${0}  timeout=60
	Wait For Trace On Uart	named_event  name=thread_b  arg0=${1}  timeout=60
	Wait For Trace On Uart	named_event  name=thread_c  arg0=${2}  timeout=60
	Wait For Trace On Uart	named_event  name=thread_d  arg0=${3}  timeout=60

	Trace Tester Close Socket
