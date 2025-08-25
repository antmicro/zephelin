cmake_minimum_required(VERSION 3.20.0)

set(RENODE_SCRIPT ${CMAKE_CURRENT_LIST_DIR}/boards/stm32f746g_disco_lis2ds12.resc)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(app)
target_sources(app PRIVATE src/main.c)

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../common/tvm ${CMAKE_CURRENT_BINARY_DIR}/tvm)
target_link_libraries(app PRIVATE tvm_model)
