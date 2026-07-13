#!/bin/bash

# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

set -xeuo pipefail

export ZEPHYR_SDK_VERSION=1.0.1

wget -N --progress=dot:giga https://dl.antmicro.com/projects/renode/zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_gnu.tar.xz -O zephyr-sdk.tar.gz && \
    mkdir -p /opt/zephyr-sdk && \
    tar -xf zephyr-sdk.tar.gz --strip 1 -C /opt/zephyr-sdk && \
    rm zephyr-sdk.tar.gz

west init -l .
west update
uv pip install -r ../zephyr/scripts/requirements.txt
west patch apply
west zephyr-export
