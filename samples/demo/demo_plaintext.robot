*** Settings ***
Resource			${KEYWORDS}

*** Test Cases ***
Should Display Demo Traces
	Prepare Machine

	Wait For Line On Uart	zpl_inference_enter
	Wait For Line On Uart	zpl_tvm_enter_event
	Wait For Line On Uart	zpl_tvm_exit_event
	Wait For Line On Uart	zpl_inference_exit
	Wait For Line On Uart	sys_trace_isr_enter
	Wait For Line On Uart	sys_trace_isr_exit
	Wait For Line On Uart	zpl_memory_event
	Wait For Line On Uart	zpl_cpu_load
