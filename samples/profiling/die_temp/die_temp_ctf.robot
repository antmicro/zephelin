*** Variables ***
${SOCKET_PORT}                      4321
@{DIE_TEMP}                         ${0.0}	${NaN}

*** Settings ***
Resource			${KEYWORDS}
Resource			../../common/socket.robot
Library				../../../tests/TraceTester.py

*** Test Cases ***
Should Display DIE Temp
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Wait For Trace On Uart	zpl_die_temp_event	die_temp=${DIE_TEMP}
	Wait For Trace On Uart	zpl_die_temp_event	die_temp=${DIE_TEMP}

	Trace Tester Close Socket
