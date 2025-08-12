*** Settings ***
Resource			${KEYWORDS}
Resource			../../common/socket.robot
Resource			common.resource
Library				../../../tests/TraceTester.py

*** Variables ***
${SOCKET_PORT}                      4321
${ENTER_MAIN_FUNCTION}                   Entered main function

*** Test Cases ***
Should Print Enabled Scope Events
	Prepare Machine
	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}
	Start Emulation

	Wait For Trace On Uart  zpl_scope_enter  scope_name=code_scope3  cycles=any  thread_id=any  timeout=20
	Wait For Trace On Uart  zpl_scope_exit   scope_name=code_scope3  cycles=any  thread_id=any  timeout=20

	Wait For Trace On Uart  zpl_scope_enter  scope_name=code_scope4  cycles=any  thread_id=any  timeout=30
	Wait For Trace On Uart  zpl_scope_exit   scope_name=code_scope4  cycles=any  thread_id=any  timeout=30

	Trace Should Not Be On Uart  zpl_scope_enter  scope_name=code_scope1
	Trace Should Not Be On Uart  zpl_scope_enter  scope_name=code_scope2

	Trace Tester Close Socket

Should Disable Code Scopes In Memory
	Prepare Machine
	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}
	Create Log Tester  1
	Execute Command  cpu0 AddSymbolHook "main" 'self.Log(LogLevel.Info, "${ENTER_MAIN_FUNCTION}")'
	Start Emulation

	Wait For Log Entry  ${ENTER_MAIN_FUNCTION}  pauseEmulation=true

	Change Code Scope State In Memory  code_scope1  disable
	Change Code Scope State In Memory  code_scope2  disable
	Change Code Scope State In Memory  code_scope3  disable
	Change Code Scope State In Memory  code_scope4  disable

	Trace Should Not Be On Uart  zpl_scope_enter
	Trace Should Not Be On Uart  zpl_scope_exit

Should Enable Code Scopes In Memory
	Prepare Machine
	Set Up Socket Terminal
	Trace Tester Open Socket	${SOCKET_PORT}
	Create Log Tester  1
	Execute Command  cpu0 AddSymbolHook "main" 'self.Log(LogLevel.Info, "${ENTER_MAIN_FUNCTION}")'
	Start Emulation

	Wait For Log Entry  ${ENTER_MAIN_FUNCTION}  pauseEmulation=true

	Change Code Scope State In Memory  code_scope1  enable
	Change Code Scope State In Memory  code_scope2  enable
	Change Code Scope State In Memory  code_scope3  enable
	Change Code Scope State In Memory  code_scope4  enable

	Wait For Trace On Uart  zpl_scope_enter  scope_name=code_scope3  cycles=any  thread_id=any  timeout=30
	Wait For Trace On Uart  zpl_scope_exit   scope_name=code_scope3  cycles=any  thread_id=any  timeout=30

	Wait For Trace On Uart  zpl_scope_enter  scope_name=code_scope1  cycles=any  thread_id=any  timeout=30
	Wait For Trace On Uart  zpl_scope_exit   scope_name=code_scope1  cycles=any  thread_id=any  timeout=30

	Wait For Trace On Uart  zpl_scope_enter  scope_name=code_scope2  cycles=any  thread_id=any  timeout=30
	Wait For Trace On Uart  zpl_scope_exit   scope_name=code_scope2  cycles=any  thread_id=any  timeout=30

	Wait For Trace On Uart  zpl_scope_enter  scope_name=code_scope4  cycles=any  thread_id=any  timeout=30
	Wait For Trace On Uart  zpl_scope_exit   scope_name=code_scope4  cycles=any  thread_id=any  timeout=30
