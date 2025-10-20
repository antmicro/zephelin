zephyr_library_named(tvm_model)
zephyr_library_sources(src/model.c src/magic_wand.c src/platform.c)
if(CONFIG_ZPL_SAMPLE_TVM_QUANTIZED_MODEL)
  zephyr_library_sources(src/sine.c)
endif()
zephyr_library_link_libraries(kernel)
zephyr_include_directories("${CMAKE_CURRENT_BINARY_DIR}/src" "${CMAKE_CURRENT_SOURCE_DIR}/src")

# Generates model specific data for microTVM, using magic-wand if `quantized` is not selected,
# or using sine otherwise
function(generate_tvm_model quantized)

set(suffix "")
set(model_name "magic-wand")
if(${quantized})
  set(suffix "_int8")
  set(model_name "sine")
endif()

set(model_path_graph "${CMAKE_CURRENT_LIST_DIR}/model/${model_name}-graph.json")
set(model_path_params "${CMAKE_CURRENT_LIST_DIR}/model/${model_name}-params.bin")

add_custom_command(
  OUTPUT
    model_graph${suffix}_min.json
  DEPENDS
    ${model_path_graph}
  COMMAND
    cat ${model_path_graph} |
      tr -d \"\\n\\t \" 1>model_graph${suffix}_min.json
)

# generate header with model data
add_custom_command(
  OUTPUT
    src/generated/model_data${suffix}_graph.h
    src/generated/model_data${suffix}_params.h
  DEPENDS
    model_graph${suffix}_min.json
    ${model_path_params}
  COMMAND
    cp model_graph${suffix}_min.json model_data${suffix}_graph
  COMMAND
    xxd -i model_data${suffix}_graph src/generated/model_data${suffix}_graph.h
  COMMAND
    rm model_data${suffix}_graph
  COMMAND
    sed -i -e "'s/unsigned/const unsigned/g'"
      src/generated/model_data${suffix}_graph.h
  COMMAND
    sed -i -e "'s/const unsigned char/const unsigned char __attribute((aligned(32)))/g'"
      src/generated/model_data${suffix}_graph.h
  COMMAND
    cp ${model_path_params} model_data${suffix}_params
  COMMAND
    xxd -i model_data${suffix}_params src/generated/model_data${suffix}_params.h
  COMMAND
    rm model_data${suffix}_params
  COMMAND
    sed -i -e "'s/unsigned/const unsigned/g'"
      src/generated/model_data${suffix}_params.h
  COMMAND
    sed -i -e "'s/const unsigned char/const unsigned char __attribute((aligned(32)))/g'"
      src/generated/model_data${suffix}_params.h
)

add_custom_target(
  generate_model_data${suffix}_h
  DEPENDS
    src/generated/model_data${suffix}_graph.h
    src/generated/model_data${suffix}_params.h
)

add_dependencies(tvm_model generate_model_data${suffix}_h)
endfunction()

generate_tvm_model(false)

if(CONFIG_ZPL_SAMPLE_TVM_QUANTIZED_MODEL)
  generate_tvm_model(true)
endif()
