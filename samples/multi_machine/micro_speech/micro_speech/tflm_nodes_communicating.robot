# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

*** Settings ***
Library         OperatingSystem
Library         RenodeLibrary

Resource        ../../multiple_machines.resource

*** Test Cases ***
Should Execute Inference Pipeline Across Two Nodes
    ${micro_speech_elf}=    Join Path    ${EXECDIR}    ${SYSBUILD_DIR}    micro_speech    zephyr    zephyr.elf
    ${preprocessor_elf}=    Join Path    ${EXECDIR}    ${SYSBUILD_DIR}    preprocessor    zephyr    zephyr.elf
    ${board_repl}=    Join Path    ${CURDIR}    ..    ..    boards    max32650fthr.repl
    ${shared_clock_repl}=    Join Path    ${CURDIR}    ..    ..    shared_clock.repl


    Setup Multi Machine
        ...    machine1_name=node_0
        ...    machine1_elf=${micro_speech_elf}
        ...    machine2_name=node_1
        ...    machine2_elf=${preprocessor_elf}
        ...    board_repl_path=${board_repl}
        ...    shared_clock_repl=${shared_clock_repl}
        ...    uart_connection=sysbus.uart1

    Start Emulation

    Wait For Line On Uart    PREPROCESSOR STATRING...             testerId=3

    Wait For Line On Uart    Buffer full. Running inference...    testerId=2    timeout=10.0

    Wait For Line On Uart    Inference complete. Results:         testerId=2
    Wait For Line On Uart    silence:                             testerId=2
