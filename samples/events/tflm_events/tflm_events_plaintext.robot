*** Settings ***
Resource			${KEYWORDS}

*** Test Cases ***
Should Display TFLM Events
	Prepare Machine

	Wait For Line On Uart	zpl_tflm_enter_event:
	Wait For Line On Uart	zpl_tflm_exit_event:
