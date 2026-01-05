*** Variables ***
${SOCKET_PORT}    4321

*** Settings ***
Resource          ${KEYWORDS}
Resource          common.resource

*** Test Cases ***
Should Display Traces With Correct Timestamps
  Prepare Machine

  FOR  ${i}   IN RANGE  2   12
    Wait For Line On Uart  tick ${i}
  END
  Wait For Line On Uart  nested2_enter 14
  Wait For Line On Uart  nested2_enter 17
  Wait For Line On Uart  top 18
  Wait For Line On Uart  nested2_exit 19
  Wait For Line On Uart  nested2_exit 22
