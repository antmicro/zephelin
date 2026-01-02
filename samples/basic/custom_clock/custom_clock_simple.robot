*** Settings ***
Resource            ${KEYWORDS}
Resource            common.resource
Resource            ../../common/socket.robot
Library             ../../common/TraceTester.py

*** Variables ***
${SOCKET_PORT}                      4321

*** Test Cases ***
Should Display Traces
  Prepare Machine
  Set Up Socket Terminal
  Trace Tester Open Socket  ${SOCKET_PORT}
  Start Emulation

  Wait For Trace On Uart  thread_info
  Wait For Tick Traces On Uart
  Wait For Nested Traces On Uart

  Trace Tester Close Socket
