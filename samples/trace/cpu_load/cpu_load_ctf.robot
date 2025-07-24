*** Variables ***
${SOCKET_PORT}                      4321

*** Settings ***
Resource			${KEYWORDS}
Resource			../common/socket.robot
Library				../../../tests/TraceTester.py

*** Test Cases ***
Should Display CPU Load
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Wait For Trace On Uart	zpl_cpu_load_event	cpu_load=${1000}
	Wait For Trace On Uart	zpl_cpu_load_event	cpu_load=any

	Trace Tester Close Socket
