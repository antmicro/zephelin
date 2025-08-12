*** Variables ***
${ZEPHYR_INSTRUMENTATION_SCRIPT}    scripts/zaru.py
${SOCKET_PORT}                      4321
${TRIGGER_FUNCTION}                 loop

*** Settings ***
Resource                            ${KEYWORDS}
Resource                            ../../common/socket.robot
Library                             zaru_helper.py

*** Keywords ***
Wait For TFLM Sample Output
  FOR  ${i}  IN RANGE  0  10
    Wait For Line On Uart       x_value: \\d+.\\d+, y_value: \\d+.\\d+        treatAsRegex=true
  END

*** Test Cases ***
Instrumentation Should Respond To Ping
	Prepare Machine

  Wait For TFLM Sample Output

  Write Line To Uart       ping             waitForEcho=False
  Wait For Line On Uart    pong

Instrumentation Should Return Enabled Status
  Prepare Machine

  Set Up Socket Terminal

  Start Emulation
  Check Instrumentation Enabled Status         %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}

Instrumentation Should Generate Callgraph
  Prepare Machine

  Set Up Socket Terminal

  Wait For TFLM Sample Output

  Start Emulation
  Check Instrumentation Enabled Status       %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}
  Set Instrumentation Coupled Trigger        %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}   ${TRIGGER_FUNCTION}
  Trigger Instrumentation Reboot             %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}

  Wait For TFLM Sample Output

  Start Emulation
  Check Instrumentation Enabled Status       %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}
  Generate Instrumentation Callgraph         %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}
  Trigger Instrumentation Reboot             %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}

Instrumentation Should Generate Perfetto Trace
  Prepare Machine

  Set Up Socket Terminal

  Wait For TFLM Sample Output

  Start Emulation
  Check Instrumentation Enabled Status       %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}
  Set Instrumentation Coupled Trigger        %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}   ${TRIGGER_FUNCTION}
  Trigger Instrumentation Reboot             %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}

  Wait For TFLM Sample Output

  Start Emulation
  Check Instrumentation Enabled Status       %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}
  Generate Instrumentation Perfetto Trace    %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}
