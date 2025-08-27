*** Settings ***
Resource			${KEYWORDS}

*** Test Cases ***
Should Display TFLM Events
	Prepare Machine

	Wait For Line On Uart	zpl_tflm_begin_event: subgraph_idx=0 op_idx=0 tag=CONV_2D
	Wait For Line On Uart	zpl_tflm_end_event: subgraph_idx=0 op_idx=0 tag=CONV_2D
	Wait For Line On Uart	zpl_tflm_begin_event: subgraph_idx=0 op_idx=1 tag=MAX_POOL_2D
	Wait For Line On Uart	zpl_tflm_end_event: subgraph_idx=0 op_idx=1 tag=MAX_POOL_2D
	Wait For Line On Uart	zpl_tflm_begin_event: subgraph_idx=0 op_idx=2 tag=CONV_2D
	Wait For Line On Uart	zpl_tflm_end_event: subgraph_idx=0 op_idx=2 tag=CONV_2D
	Wait For Line On Uart	zpl_tflm_begin_event: subgraph_idx=0 op_idx=3 tag=MAX_POOL_2D
	Wait For Line On Uart	zpl_tflm_end_event: subgraph_idx=0 op_idx=3 tag=MAX_POOL_2D
	Wait For Line On Uart	zpl_tflm_begin_event: subgraph_idx=0 op_idx=4 tag=RESHAPE
	Wait For Line On Uart	zpl_tflm_end_event: subgraph_idx=0 op_idx=4 tag=RESHAPE
	Wait For Line On Uart	zpl_tflm_begin_event: subgraph_idx=0 op_idx=5 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_end_event: subgraph_idx=0 op_idx=5 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_begin_event: subgraph_idx=0 op_idx=6 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_end_event: subgraph_idx=0 op_idx=6 tag=FULLY_CONNECTED
	Wait For Line On Uart	zpl_tflm_begin_event: subgraph_idx=0 op_idx=7 tag=SOFTMAX
	Wait For Line On Uart	zpl_tflm_end_event: subgraph_idx=0 op_idx=7 tag=SOFTMAX
