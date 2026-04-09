# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(zpl_test)

zephyr_include_directories(include)

if(CONFIG_ZPL_BENCHMARK_RUN_DHRYSTONE)
    set(bench_src "src/benchmarks/dhrystone.c")
elseif(CONFIG_ZPL_BENCHMARK_RUN_BASIC)
    set(bench_src "src/benchmarks/basic.c")
elseif(CONFIG_ZPL_BENCHMARK_RUN_THREADS)
    set(bench_src "src/benchmarks/threads.c")
endif()

target_sources(app PRIVATE src/main.c ${bench_src})
