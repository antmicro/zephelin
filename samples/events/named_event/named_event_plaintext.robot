*** Settings ***
Resource			${KEYWORDS}

*** Test Cases ***
Should Display Function Name
	Prepare Machine

	Wait For Line On Uart	zpl_named_event
