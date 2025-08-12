*** Variables ***
${MEMORY_ADDRESS}       0[xX][0-9a-fA-F]+

*** Keywords ***
Change Code Scope State In Memory
	[Arguments]           ${scope}  ${state}
	${CODE_SCOPE_ADDR}=  Execute Command  sysbus GetSymbolAddress "${scope}"
	${CODE_SCOPE_ADDR}=  Convert To Integer  ${CODE_SCOPE_ADDR}
	${CODE_SCOPE_ADDR}=  Evaluate  ${CODE_SCOPE_ADDR} + 4
	IF  "${state}" == "enable"
		Execute Command  sysbus WriteDoubleWord ${CODE_SCOPE_ADDR} 0x01
	ELSE
		Execute Command  sysbus WriteDoubleWord ${CODE_SCOPE_ADDR} 0x00
	END


Change Code Scope State From Uart
	[Arguments]           ${scope}  ${state}
	Write Line To Uart  dynamic_conf ${state} ${scope}  waitForEcho=false
