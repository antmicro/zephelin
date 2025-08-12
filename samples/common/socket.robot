*** Keywords ***
Set Up Socket Terminal
  Execute Command          emulation CreateServerSocketTerminal ${SOCKET_PORT} "term" False
  Execute Command          connector Connect ${UART} "term"
