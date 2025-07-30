*** Settings ***
Resource			${KEYWORDS}

*** Test Cases ***
Should Display Layer Profiling Traces
	Prepare Machine

	Wait For Line On Uart	zpl_inference_enter:
	Wait For Line On Uart	zpl_tflm_enter_event: subgraph_idx=0 op_idx=0 tag=CONV_2D
	Wait For Line On Uart	zpl_tflm_exit_event: subgraph_idx=0 op_idx=0 tag=CONV_2D
	Wait For Line On Uart	zpl_tflm_enter_event: subgraph_idx=0 op_idx=1 tag=MAX_POOL_2D
	Wait For Line On Uart	zpl_tflm_exit_event: subgraph_idx=0 op_idx=1 tag=MAX_POOL_2D
	Wait For Line On Uart	zpl_tflm_enter_event: subgraph_idx=0 op_idx=2 tag=CONV_2D
	Wait For Line On Uart	zpl_tflm_exit_event: subgraph_idx=0 op_idx=2 tag=CONV_2D
	Wait For Line On Uart	zpl_tflm_enter_event: subgraph_idx=0 op_idx=3 tag=MAX_POOL_2D
	Wait For Line On Uart	zpl_tflm_exit_event: subgraph_idx=0 op_idx=3 tag=MAX_POOL_2D
	Wait For Line On Uart	zpl_tflm_enter_event: subgraph_idx=0 op_idx=4 tag=RESHAPE
	Wait For Line On Uart	zpl_tflm_exit_event: subgraph_idx=0 op_idx=4 tag=RESHAPE
	Wait For Line On Uart	zpl_tflm_enter_event: subgraph_idx=0 op_idx=5 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_exit_event: subgraph_idx=0 op_idx=5 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_enter_event: subgraph_idx=0 op_idx=6 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_exit_event: subgraph_idx=0 op_idx=6 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_enter_event: subgraph_idx=0 op_idx=7 tag=SOFTMAX
	Wait For Line On Uart	zpl_tflm_exit_event: subgraph_idx=0 op_idx=7 tag=SOFTMAX
	Wait For Line On Uart	zpl_inference_exit:
	Wait For Line On Uart	zpl_memory_event

Should Not Display Full Traces
	Prepare Machine

	Should Not Be On Uart	sys_trace	timeout=10
