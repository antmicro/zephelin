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
Should Display CPU Load
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Wait For Trace On Uart	zpl_cpu_load_event	cpu_load=${1000}
	Wait For Trace On Uart	zpl_cpu_load_event	cpu_load=any

	Trace Tester Close Socket
