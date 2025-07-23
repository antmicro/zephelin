cmake_minimum_required(VERSION 3.20.0)

include(${CMAKE_CURRENT_LIST_DIR}/../common/boards.cmake)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(app)
target_sources(app PRIVATE ../common/src/main.c)
