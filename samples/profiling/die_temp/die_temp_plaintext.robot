*** Settings ***
Resource			${KEYWORDS}

*** Test Cases ***
Should Display DIE Temperature
	Prepare Machine

	Wait For Line On Uart	zpl_die_temp_event: die_temp[0]=
