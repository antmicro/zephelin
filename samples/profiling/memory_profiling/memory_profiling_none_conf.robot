*** Settings ***
Resource			${KEYWORDS}

*** Test Cases ***
Should Display Memory Usage
	Prepare Machine
	Run Keyword And Expect Error  *Terminal tester failed*  Wait For Line On Uart  zpl_memory_event  timeout=5
