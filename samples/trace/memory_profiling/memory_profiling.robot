*** Settings ***
Resource			${KEYWORDS}
Resource			common_keywords.resource

*** Test Cases ***
Should Display Memory Usage
	Prepare Machine

	Wait For Line On Uart	zpl_named_event: counter (5; 0)
	Wait For Memory Event On Uart

	Wait For Line On Uart	zpl_named_event: counter (4; 0)
	Wait For Memory Event On Uart

	Wait For Line On Uart	zpl_named_event: counter (3; 0)
	Wait For Memory Event On Uart

	Wait For Line On Uart	zpl_named_event: counter (2; 0)
	Wait For Memory Event On Uart

	Wait For Line On Uart	zpl_named_event: counter (1; 0)
	Wait For Memory Event On Uart
