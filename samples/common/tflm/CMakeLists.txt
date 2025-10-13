# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

zephyr_library_named(tflm_model)
zephyr_library_sources(src/model.cpp)
zephyr_include_directories("${CMAKE_CURRENT_BINARY_DIR}/src" "${CMAKE_CURRENT_SOURCE_DIR}/src")

# generate header with model data

set(i 0)
foreach(MODEL_NAME IN LISTS CONFIG_ZPL_SAMPLE_TFLM_MODEL)

  set(model_path "${CMAKE_CURRENT_LIST_DIR}/model/${MODEL_NAME}.tflite")
  set(generated_model_data "src/generated/model${i}_data.h")
  message(STATUS "Generating model data for ${MODEL_NAME} to ${generated_model_data}")

  add_custom_command(
    OUTPUT
      ${generated_model_data}
    DEPENDS
      ${model_path}
    COMMAND
      cp ${model_path} model${i}_data
    COMMAND
      xxd -i model${i}_data ${generated_model_data}
    COMMAND
      rm model${i}_data
    COMMAND
      sed -i -e "'s/unsigned/const unsigned/g'"
        ${generated_model_data}
    COMMAND
      sed -i -e "'s/const unsigned char/const unsigned char __attribute((aligned(32)))/g'"
        ${generated_model_data}
    COMMAND
      sed -i -e "'s/model_data/model${i}_data/g'"
        ${generated_model_data}
  )

  add_custom_target(
    generate_model${i}_data_h
    DEPENDS
      ${generated_model_data}
  )

  add_dependencies(tflm_model generate_model${i}_data_h)

  math(EXPR i "${i}+1")

endforeach()
