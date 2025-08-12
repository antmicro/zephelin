*** Settings ***
Resource			${KEYWORDS}
Resource			common_keywords.resource

*** Keywords ***
Change Memory Usage Config
	[Arguments]		${state}
	Write Line To Uart  mem_usage_trace ${state}  waitForEcho=false

*** Test Cases ***
Should Display Memory Usage
	Prepare Machine
	Test Runtime Config
