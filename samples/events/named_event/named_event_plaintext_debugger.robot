*** Settings ***
Resource			${KEYWORDS}
Library				gdb_helper.py

*** Test Cases ***
Should Display Function Name
	Prepare Machine

	Create Log Tester	1
	Execute Command		pause
	Execute Command		machine StartGdbServer 3333
	Execute Command		cpu0 LogFunctionNames true
	Execute Command		start

	Wait For Log Entry	Entering function zpl_named_event
	Wait For Log Entry	Entering function zpl_named_event

	Gdb Dump Trace Data	%{ZPL_BASE}/scripts/dump_trace.gdb	${ELF}
	Gdb Verify Trace Data	named_event
