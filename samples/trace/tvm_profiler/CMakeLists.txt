cmake_minimum_required(VERSION 3.20.0)

include(${CMAKE_CURRENT_SOURCE_DIR}/../common/boards.cmake)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(app)
target_sources(app PRIVATE src/main.c src/model.c src/platform.c src/magic_wand.c)
include_directories("${CMAKE_CURRENT_BINARY_DIR}/src" "${CMAKE_CURRENT_SOURCE_DIR}/src")

# generate header with model data

set(model_path_graph "${CMAKE_CURRENT_LIST_DIR}/model/magic-wand-graph.json")
set(model_path_params "${CMAKE_CURRENT_LIST_DIR}/model/magic-wand-params.bin")

add_custom_command(
  OUTPUT
    model_graph_min.json
  DEPENDS
    ${model_path_graph}
  COMMAND
    cat ${model_path_graph} |
      tr -d \"\\n\\t \" 1>model_graph_min.json
)

add_custom_command(
  OUTPUT
    src/generated/model_data_graph.h
    src/generated/model_data_params.h
  DEPENDS
    model_graph_min.json
    ${model_path_params}
  COMMAND
    cp model_graph_min.json model_data_graph
  COMMAND
    xxd -i model_data_graph src/generated/model_data_graph.h
  COMMAND
    rm model_data_graph
  COMMAND
    sed -i -e "'s/unsigned/const unsigned/g'"
      src/generated/model_data_graph.h
  COMMAND
    sed -i -e "'s/const unsigned char/const unsigned char __attribute((aligned(32)))/g'"
      src/generated/model_data_graph.h
  COMMAND
    cp ${model_path_params} model_data_params
  COMMAND
    xxd -i model_data_params src/generated/model_data_params.h
  COMMAND
    rm model_data_params
  COMMAND
    sed -i -e "'s/unsigned/const unsigned/g'"
      src/generated/model_data_params.h
  COMMAND
    sed -i -e "'s/const unsigned char/const unsigned char __attribute((aligned(32)))/g'"
      src/generated/model_data_params.h
)

add_custom_target(
  generate_model_data_h
  DEPENDS
    src/generated/model_data_graph.h
    src/generated/model_data_params.h
)

add_dependencies(app generate_model_data_h)
