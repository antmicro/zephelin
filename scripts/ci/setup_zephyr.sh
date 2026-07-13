#!/bin/bash

# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

set -xeuo pipefail

wget -N --progress=dot:giga https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.17.2/zephyr-sdk-0.17.2_linux-x86_64.tar.xz -O zephyr-sdk.tar.gz && \
    mkdir -p /opt/zephyr-sdk && \
    tar -xf zephyr-sdk.tar.gz --strip 1 -C /opt/zephyr-sdk && \
    rm zephyr-sdk.tar.gz

west init -l .
west update
uv pip install -r ../zephyr/scripts/requirements.txt
west patch apply
west zephyr-export
