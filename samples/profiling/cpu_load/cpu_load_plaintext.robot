*** Settings ***
Resource			${KEYWORDS}

*** Test Cases ***
Should Display CPU Load
	Prepare Machine

	Wait For Line On Uart	zpl_cpu_load_event: cpu_load=100.0%
