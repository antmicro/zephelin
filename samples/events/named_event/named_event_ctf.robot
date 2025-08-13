*** Variables ***
${SOCKET_PORT}                      4321

*** Settings ***
Resource			${KEYWORDS}
Resource			../../common/socket.robot
Library				../../common/TraceTester.py

*** Test Cases ***
Should Display Function Name
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

	Wait For Trace On Uart	named_event	name=counter_value	arg0=${0}	arg1=${0}
	Wait For Trace On Uart	named_event	name=counter_value	arg0=${1}	arg1=${0}
	Wait For Trace On Uart	named_event	name=counter_value	arg0=${2}	arg1=${0}
	Wait For Trace On Uart	named_event	name=counter_value	arg0=${3}	arg1=${0}
	Wait For Trace On Uart	named_event	name=counter_value	arg0=${4}	arg1=${0}
	Wait For Trace On Uart	named_event	name=counter_value	arg0=${5}	arg1=${0}
	Wait For Trace On Uart	named_event	name=counter_value	arg0=${6}	arg1=${0}
	Wait For Trace On Uart	named_event	name=counter_value	arg0=${7}	arg1=${0}
	Wait For Trace On Uart	named_event	name=counter_value	arg0=${8}	arg1=${0}
	Wait For Trace On Uart	named_event	name=counter_value	arg0=${9}	arg1=${0}

	Trace Tester Close Socket
