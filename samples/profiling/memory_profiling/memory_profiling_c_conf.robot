*** Settings ***
Resource			${KEYWORDS}
Resource			common_keywords.resource

*** Keywords ***
Change Memory Usage Config
	[Arguments]		${_}
	No Operation

*** Test Cases ***
Should Display Memory Usage
	Prepare Machine
	Test Runtime Config
