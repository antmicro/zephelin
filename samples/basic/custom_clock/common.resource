*** Keywords ***
Wait For Tick Trace On Uart
  [Arguments]           ${i}  ${ts}=${None}
  IF  '${ts}' != 'None'
    Wait For Trace On Uart            named_event   name=tick   arg0=${i}   timestamp=${ts}
    ${ret}=   Evaluate  ${ts} + 1
  ELSE
    ${ts}=    Wait For Trace On Uart  named_event   name=tick   arg0=${i}
    ${ret}=   Set Variable  ${None}
  END
  [Return]  ${ret}

Wait For Tick Traces On Uart
  [Arguments]           ${ts}=${None}
  FOR  ${i}   IN RANGE  0   10
      ${ts}=  Wait For Tick Trace On Uart    i=${i}    ts=${ts}
  END
  [Return]  ${ts}

Wait For Memory Trace On Uart
  [Arguments]           ${ts}=${None}
  IF  '${ts}' != 'None'
    Wait For Trace On Uart  zpl_memory  timestamp=${ts}
    ${ret}=   Evaluate  ${ts} + 1
  ELSE
    Wait For Trace On Uart  zpl_memory
    ${ret}=   Set Variable  ${None}
  END
  [Return]  ${ret}

Wait For Memory Traces On Uart
  [Arguments]           ${ts}=${None}
  ${ts}=  Wait For Memory Trace On Uart   ${ts}
  ${ts}=  Wait For Memory Trace On Uart   ${ts}
  ${ts}=  Wait For Memory Trace On Uart   ${ts}
  ${ts}=  Wait For Memory Trace On Uart   ${ts}

  [Return]  ${ts}

Wait For Nested Traces On Uart
  [Arguments]           ${ts}=${None}
  IF  '${ts}' != 'None'
    Wait For Trace On Uart  zpl_scope_enter   scope_name=nested_scope1  timestamp=${ts}
    Wait For Trace On Uart  zpl_scope_enter   scope_name=nested_scope2  timestamp=${${ts} + 1}
    Wait For Trace On Uart  named_event       name=top                  timestamp=${${ts} + 2}
    Wait For Trace On Uart  zpl_scope_exit    scope_name=nested_scope2  timestamp=${${ts} + 3}
    Wait For Trace On Uart  zpl_scope_exit    scope_name=nested_scope1  timestamp=${${ts} + 4}
  ELSE
    Wait For Trace On Uart  zpl_scope_enter   scope_name=nested_scope1
    Wait For Trace On Uart  zpl_scope_enter   scope_name=nested_scope2
    Wait For Trace On Uart  named_event       name=top
    Wait For Trace On Uart  zpl_scope_exit    scope_name=nested_scope2
    Wait For Trace On Uart  zpl_scope_exit    scope_name=nested_scope1
  END
