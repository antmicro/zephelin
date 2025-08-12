*** Settings ***
Resource			${KEYWORDS}
Resource			common_keywords.resource

*** Keywords ***
Change Memory Usage Config
	[Arguments]		${state}

	${DEBUG_CONFIGS_ADDR}=  Execute Command  sysbus GetSymbolAddress "debug_configs"

  IF  "${state}" == "enable"
    Execute Command  sysbus WriteWord ${DEBUG_CONFIGS_ADDR} 0x0101
  ELSE
    Execute Command  sysbus WriteWord ${DEBUG_CONFIGS_ADDR} 0x0000
  END

*** Test Cases ***
Should Display Memory Usage
	Prepare Machine
	Test Runtime Config
