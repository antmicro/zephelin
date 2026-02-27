*** Settings ***
Library         OperatingSystem
Library         RenodeLibrary

*** Keywords ***
Setup Multi Machine
    [Arguments]    ${machine1_name}    ${machine1_elf}    ${machine2_name}    ${machine2_elf}    ${board_repl_path}    ${shared_clock_repl}=${EMPTY}    ${uart_connection}=${EMPTY}

    ${mach1_elf}=    Normalize Path    ${machine1_elf}
    ${mach2_elf}=    Normalize Path    ${machine2_elf}
    ${board_repl}=   Normalize Path    ${board_repl_path}

    File Should Exist    ${mach1_elf}    msg=ERROR: ${machine1_name} ELF not found
    File Should Exist    ${mach2_elf}    msg=ERROR: ${machine2_name} ELF not found
    File Should Exist    ${board_repl}   msg=ERROR: Board REPL not found at ${board_repl}

    ${shared_clock_cmd}=    Set Variable    ${EMPTY}
    IF    '${shared_clock_repl}' != '${EMPTY}'
        ${shared_clock}=    Normalize Path    ${shared_clock_repl}
        File Should Exist   ${shared_clock}    msg=ERROR: Shared clock REPL not found
        ${shared_clock_cmd}=    Set Variable    machine LoadPlatformDescription @${shared_clock}
    END

    ${create_hub_cmd}=    Set Variable    ${EMPTY}
    ${connect_uart_cmd}=  Set Variable    ${EMPTY}
    IF    '${uart_connection}' != '${EMPTY}'
        ${create_hub_cmd}=    Set Variable    emulation CreateUARTHub "uart_hub"
        ${connect_uart_cmd}=  Set Variable    connector Connect ${uart_connection} uart_hub
    END


    ${var_script_content}=    Catenate    SEPARATOR=\n
        ...    ${create_hub_cmd}
        ...    mach create "${machine1_name}"
        ...    machine LoadPlatformDescription @${board_repl}
        ...    ${shared_clock_cmd}
        ...    ${connect_uart_cmd}
        ...    sysbus LoadELF @${mach1_elf}
        ...    mach create "${machine2_name}"
        ...    machine LoadPlatformDescription @${board_repl}
        ...    ${shared_clock_cmd}
        ...    ${connect_uart_cmd}
        ...    sysbus LoadELF @${mach2_elf}

    ${var_script_path}=    Join Path    ${OUTPUT DIR}    load_vars.resc
    Create File    ${var_script_path}    ${var_script_content}

    Execute Script  ${var_script_path}

    Create Terminal Tester  sysbus.uart0  machine=${machine1_name}
    Create Terminal Tester  sysbus.uart0  machine=${machine2_name}

    Create Terminal Tester  sysbus.uart2  machine=${machine1_name}
    Create Terminal Tester  sysbus.uart2  machine=${machine2_name}
