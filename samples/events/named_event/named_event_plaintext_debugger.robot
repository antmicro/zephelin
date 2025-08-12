*** Settings ***
Resource			${KEYWORDS}
Library				gdb_helper.py

*** Test Cases ***
Should Display Function Name
	Prepare Machine

	Execute Command		pause
	Execute Command		machine StartGdbServer 3333
	Execute Command		start

	Gdb Dump Trace Data	%{ZPL_BASE}/scripts/dump_trace.gdb	${ELF}
	Gdb Verify Trace Data	named_event
