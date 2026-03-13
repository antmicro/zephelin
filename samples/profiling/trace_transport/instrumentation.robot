*** Variables ***
${ZEPHYR_INSTRUMENTATION_SCRIPT}    scripts/instrumentation/zaru.py
${SOCKET_PORT}                      4321

*** Settings ***
Resource                            ${KEYWORDS}
Resource                            ../../common/socket.robot
Library				                      ../../common/TraceTester.py
Library                             ../../common/elf_util.py

*** Test Cases ***
Instrumentation Should Send CTF
  Prepare Machine

  Set Up Socket Terminal

  Start Emulation

  Trace Tester Open Socket    ${SOCKET_PORT}

  ${SYMBOL_ADDR_MAIN} =    Elf Symbol To Address    ${ELF}    main
  ${SYMBOL_ADDR_LOOP} =    Elf Symbol To Address    ${ELF}    _Z4loopv

  Wait For Trace On Uart    func_entry_with_context    callee=${SYMBOL_ADDR_MAIN}
  Wait For Trace On Uart    func_entry_with_context    callee=${SYMBOL_ADDR_LOOP}
  Wait For Trace On Uart    func_exit_with_context    callee=${SYMBOL_ADDR_LOOP}
