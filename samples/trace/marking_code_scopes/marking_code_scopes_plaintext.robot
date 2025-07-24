*** Settings ***
Resource			${KEYWORDS}

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

*** Test Cases ***
Should Print Enabled Scope Events
	Prepare Machine

	Wait For Line On Uart  zpl_scope_enter \\d+ code_scope3 ${MEMORY_ADDRESS}  treatAsRegex=true
	Wait For Line On Uart  zpl_scope_exit \\d+ code_scope3 ${MEMORY_ADDRESS}  treatAsRegex=true

	Run Keyword And Expect Error  *Terminal tester failed*  Wait For Line On Uart  zpl_scope_enter \\d+ code_scope1  treatAsRegex=true  timeout=2
	Run Keyword And Expect Error  *Terminal tester failed*  Wait For Line On Uart  zpl_scope_enter \\d+ code_scope2  treatAsRegex=true  timeout=2

Should Disable Code Scopes In Memory
	Prepare Machine
	Wait For Line On Uart  Booting Zephyr OS

	Change Code Scope State In Memory  code_scope1  disable
	Change Code Scope State In Memory  code_scope2  disable
	Change Code Scope State In Memory  code_scope3  disable
	Change Code Scope State In Memory  code_scope4  disable

	Run Keyword And Expect Error  *Terminal tester failed*  Wait For Line On Uart  zpl_scope_enter \\d+ code_scope\d  treatAsRegex=true  timeout=2

Should Enable Code Scopes In Memory
	Prepare Machine
	Wait For Line On Uart  Booting Zephyr OS

	Change Code Scope State In Memory  code_scope1  enable
	Change Code Scope State In Memory  code_scope2  enable
	Change Code Scope State In Memory  code_scope3  enable
	Change Code Scope State In Memory  code_scope4  enable

	Wait For Line On Uart  zpl_scope_enter \\d+ code_scope3  treatAsRegex=true
	Wait For Line On Uart  zpl_scope_exit \\d+ code_scope3  treatAsRegex=true

	Wait For Line On Uart  zpl_scope_enter \\d+ code_scope1  treatAsRegex=true
	Wait For Line On Uart  zpl_scope_exit \\d+ code_scope1  treatAsRegex=true

	Wait For Line On Uart  zpl_scope_enter \\d+ code_scope2  treatAsRegex=true
	Wait For Line On Uart  zpl_scope_exit \\d+ code_scope2  treatAsRegex=true

	Wait For Line On Uart  zpl_scope_enter \\d+ code_scope4  treatAsRegex=true
	Wait For Line On Uart  zpl_scope_exit \\d+ code_scope4  treatAsRegex=true

Should Disable Code Scopes From Uart
	Prepare Machine
	Wait For Line On Uart  Booting Zephyr OS

	Change Code Scope State From Uart  code_scope1  disable
	Change Code Scope State From Uart  code_scope2  disable
	Change Code Scope State From Uart  code_scope3  disable
	Change Code Scope State From Uart  code_scope4  disable

	Run Keyword And Expect Error  *Terminal tester failed*  Wait For Line On Uart  zpl_scope_enter \\d+ code_scope\d  treatAsRegex=true  timeout=2

Should Enable Code Scopes From Uart
	Prepare Machine
	Wait For Line On Uart  Booting Zephyr OS

	Change Code Scope State From Uart  code_scope1  enable
	Change Code Scope State From Uart  code_scope2  enable
	Change Code Scope State From Uart  code_scope3  enable
	Change Code Scope State From Uart  code_scope4  enable

	Wait For Line On Uart  zpl_scope_enter \\d+ code_scope3  treatAsRegex=true
	Wait For Line On Uart  zpl_scope_exit \\d+ code_scope3  treatAsRegex=true

	Wait For Line On Uart  zpl_scope_enter \\d+ code_scope1  treatAsRegex=true
	Wait For Line On Uart  zpl_scope_exit \\d+ code_scope1  treatAsRegex=true

	Wait For Line On Uart  zpl_scope_enter \\d+ code_scope2  treatAsRegex=true
	Wait For Line On Uart  zpl_scope_exit \\d+ code_scope2  treatAsRegex=true

	Wait For Line On Uart  zpl_scope_enter \\d+ code_scope4  treatAsRegex=true
	Wait For Line On Uart  zpl_scope_exit \\d+ code_scope4  treatAsRegex=true
