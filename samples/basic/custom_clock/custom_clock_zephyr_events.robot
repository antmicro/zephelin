*** Variables ***
${SOCKET_PORT}    4321

*** Settings ***
Resource          ${KEYWORDS}
Resource          ../../common/socket.robot
Resource          common.resource
Library           ../../common/TraceTester.py

*** Test Cases ***
Should Display Traces With Correct Timestamps
  Prepare Machine
  Set Up Socket Terminal
  Trace Tester Open Socket  ${SOCKET_PORT}
  Start Emulation

  Wait For Trace On Uart  thread_info     timestamp=${1}

  ${ts}=  Wait For Memory Traces On Uart  ${2}
  ${ts}=  Wait For Tick Traces On Uart    ${ts}
  ${ts}=  Wait For Memory Traces On Uart  ${ts}

  Wait For Nested Traces On Uart          ${ts}

  Trace Tester Close Socket
