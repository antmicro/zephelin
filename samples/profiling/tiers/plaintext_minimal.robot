*** Settings ***
Resource			${KEYWORDS}

*** Test Cases ***
Should Display Minimal Traces
	Prepare Machine

	Wait For Line On Uart	zpl_inference_enter:
	Wait For Line On Uart	zpl_inference_exit:
	Wait For Line On Uart	zpl_memory_event

Should Not Display Layer Profiling Traces
	Prepare Machine

	Should Not Be On Uart	zpl_tflm_enter_event	timeout=10

Should Not Display Full Traces
	Prepare Machine

	Should Not Be On Uart	sys_trace	timeout=10
