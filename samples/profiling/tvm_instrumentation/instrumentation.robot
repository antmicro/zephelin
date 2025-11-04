*** Variables ***
${ZEPHYR_INSTRUMENTATION_SCRIPT}    scripts/zaru.py
${SOCKET_PORT}                      4321
${TRIGGER_FUNCTION}                 model_run

*** Settings ***
Resource                            ${KEYWORDS}
Resource                            ../../common/socket.robot
Library                             ../../common/instrumentation/zaru_helper.py

*** Test Cases ***
Instrumentation Should Respond To Ping
	Prepare Machine

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

  Start Emulation
  Check Instrumentation Enabled Status       %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}
  Set Instrumentation Coupled Trigger        %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}   ${TRIGGER_FUNCTION}
  Trigger Instrumentation Reboot             %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}

  Start Emulation
  Check Instrumentation Enabled Status       %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}
  Generate Instrumentation Callgraph         %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}
  Trigger Instrumentation Reboot             %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}

Instrumentation Should Generate Perfetto Trace
  Prepare Machine

  Set Up Socket Terminal

  Start Emulation
  Check Instrumentation Enabled Status       %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}
  Set Instrumentation Coupled Trigger        %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}   ${TRIGGER_FUNCTION}
  Trigger Instrumentation Reboot             %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}

  Start Emulation
  Check Instrumentation Enabled Status       %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}
  Generate Instrumentation Perfetto Trace    %{ZEPHYR_BASE}/${ZEPHYR_INSTRUMENTATION_SCRIPT}   socket://localhost:${SOCKET_PORT}
