*** Settings ***
Resource                            ${KEYWORDS}
Library                             String
Library                             OperatingSystem

*** Variables ***
${CSV}    out.csv

*** Keywords ***
Read KConfig Option
    [Arguments]    ${config_name}
    ${ret}=    Grep File    zephyr/.config    ${config_name}=
    ${val}=    Fetch From Right    ${ret}    =
    RETURN    ${val}

*** Test Cases ***
Bench Should Collect Measurements
    Prepare Machine
    Start Emulation

    ${iter_count}=    Read KConfig Option    CONFIG_ZPL_BENCHMARK_ITERS
    ${iter_count}=    Evaluate    ${iter_count} + 1
    ${magic}=         Read KConfig Option    CONFIG_ZPL_BENCHMARK_MAGIC
    ${magic}=         Strip String    ${magic}    characters="

    Create File    ${CSV}

    FOR  ${i}  IN RANGE  0  ${iter_count}
        ${result}=      Wait For Line On Uart    ${magic}
        ${csv_line}=    Fetch From Right    ${result}[Line]    ${magic}
        ${csv_line}=    Strip String    ${csv_line}
        Append To File    ${CSV}    ${csv_line}\n
    END

    Wait For Line On Uart    ${magic}
