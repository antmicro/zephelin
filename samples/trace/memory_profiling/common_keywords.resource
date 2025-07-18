*** Variables ***
${MEMORY_ADDRESS}       0[xX][0-9a-fA-F]+

*** Keywords ***
Wait For Memory Event On Uart
	Wait For Line On Uart	zpl_memory_event stack \\(${MEMORY_ADDRESS}\\) \\d+B \\d+B \\d+B  treatAsRegex=true
	Wait For Line On Uart	zpl_memory_event heap \\(${MEMORY_ADDRESS}\\) \\d+B \\d+B \\d+B  treatAsRegex=true
	Wait For Line On Uart	zpl_memory_event k_heap \\(${MEMORY_ADDRESS}\\) \\d+B \\d+B \\d+B  treatAsRegex=true
	Wait For Line On Uart	zpl_memory_event mem_slab \\(${MEMORY_ADDRESS}\\) \\d+B \\d+B \\d+B  treatAsRegex=true

Test Runtime Config
	Wait For Line On Uart	zpl_named_event: counter (5; 0)
	Wait For Line On Uart	zpl_named_event: counter (4; 0)
	Change Memory Usage Config  enable
	Wait For Line On Uart	zpl_named_event: counter (3; 0)
	Wait For Memory Event On Uart
	Wait For Line On Uart	zpl_named_event: counter (2; 0)
	Change Memory Usage Config  disable
	Wait For Line On Uart	zpl_named_event: counter (1; 0)
	Wait For Line On Uart	zpl_named_event: counter (0; 0)
	Run Keyword And Expect Error  *Terminal tester failed*  Wait For Line On Uart  zpl_memory_event  timeout=2
	Change Memory Usage Config  disable
	Change Memory Usage Config  disable
	Run Keyword And Expect Error  *Terminal tester failed*  Wait For Line On Uart  zpl_memory_event  timeout=2
	Change Memory Usage Config  enable
	Wait For Memory Event On Uart
