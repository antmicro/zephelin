*** Settings ***
Resource			${KEYWORDS}
Resource      common.resource

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
