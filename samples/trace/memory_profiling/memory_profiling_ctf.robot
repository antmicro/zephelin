*** Variables ***
${SOCKET_PORT}                      4321
${ZPL_STACK}                        ${0}
${ZPL_HEAP}                         ${1}
${ZPL_K_HEAP}                       ${2}
${ZPL_MEM_SLAB}                     ${3}

*** Settings ***
Resource			${KEYWORDS}
Resource			../common/socket.robot
Library				../../../tests/TraceTester.py

*** Test Cases ***
Should Display Memory Usage
	Prepare Machine

	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}

	Start Emulation

# Counter: 5
	Wait For Trace On Uart	named_event	name=counter	arg0=${5}
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_STACK}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_HEAP}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_K_HEAP}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_MEM_SLAB}	memory_addr=any	used=any	unused=any	for_thread_id=any

# Counter: 4
	Wait For Trace On Uart	named_event	name=counter	arg0=${4}
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_STACK}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_HEAP}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_K_HEAP}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_MEM_SLAB}	memory_addr=any	used=any	unused=any	for_thread_id=any

# Counter: 3
	Wait For Trace On Uart	named_event	name=counter	arg0=${3}
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_STACK}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_HEAP}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_K_HEAP}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_MEM_SLAB}	memory_addr=any	used=any	unused=any	for_thread_id=any

# Counter: 2
	Wait For Trace On Uart	named_event	name=counter	arg0=${2}
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_STACK}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_HEAP}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_K_HEAP}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_MEM_SLAB}	memory_addr=any	used=any	unused=any	for_thread_id=any

# Counter: 1
	Wait For Trace On Uart	named_event	name=counter	arg0=${1}
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_STACK}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_HEAP}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_K_HEAP}	memory_addr=any	used=any	unused=any	for_thread_id=any
	Wait For Trace On Uart	zpl_memory	memory_region=${ZPL_MEM_SLAB}	memory_addr=any	used=any	unused=any	for_thread_id=any

	Trace Tester Close Socket
