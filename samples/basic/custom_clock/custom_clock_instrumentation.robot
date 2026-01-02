*** Variables ***
${SOCKET_PORT}    4321

*** Settings ***
Resource          ${KEYWORDS}
Resource          common.resource

*** Test Cases ***
Should Display Traces With Correct Timestamps
  Prepare Machine

  FOR  ${i}   IN RANGE  1   11
    Wait For Line On Uart  tick ${i}
  END
  Wait For Line On Uart  nested2_enter 13
  Wait For Line On Uart  nested2_enter 16
  Wait For Line On Uart  top 17
  Wait For Line On Uart  nested2_exit 18
  Wait For Line On Uart  nested2_exit 21
