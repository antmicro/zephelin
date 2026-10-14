# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

*** Settings ***
Library         OperatingSystem
Library         RenodeLibrary
Library         ../../../common/ZephyrBuildDir.py

Resource        ../../multiple_machines.resource

*** Test Cases ***
Should Execute All Inferences On Both Nodes
    ${node_0_elf}=    Get Zephyr Image ELF    node_0
    ${node_1_elf}=    Get Zephyr Image ELF    node_1
    ${board_repl}=    Join Path    ${CURDIR}    ..    ..    boards    max32650fthr.repl
    ${shared_clock_repl}=    Join Path    ${CURDIR}    ..    ..    shared_clock.repl

    Setup Multi Machine
    ...    machine1_name=node_0
    ...    machine1_elf=${node_0_elf}
    ...    machine2_name=node_1
    ...    machine2_elf=${node_1_elf}
    ...    board_repl_path=${board_repl}
    ...    shared_clock_repl=${shared_clock_repl}

    Start Emulation

    Wait For Line On Uart    zpl_tflm_enter_event:    testerId=0
    Wait For Line On Uart    zpl_tflm_exit_event:     testerId=0
    Wait For Line On Uart    zpl_tflm_enter_event:    testerId=0
    Wait For Line On Uart    zpl_tflm_exit_event:     testerId=0

    Wait For Line On Uart    zpl_tflm_enter_event:    testerId=1
    Wait For Line On Uart    zpl_tflm_exit_event:     testerId=1
    Wait For Line On Uart    zpl_tflm_enter_event:    testerId=1
    Wait For Line On Uart    zpl_tflm_exit_event:     testerId=1
