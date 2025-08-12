*** Settings ***
Resource			${KEYWORDS}

*** Test Cases ***
Should Display Function Name
	Execute Command		$elf = ${ELF}
	Execute Command		include ${RESC}
	Create Terminal Tester	sysbus.trivial_uart  defaultPauseEmulation=True
	Write Char Delay	0.01

	Wait For Line On Uart   zpl_named_event
