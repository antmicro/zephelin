#!/bin/bash

# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

set -xeuo pipefail

source ./scripts/zephyr_version.sh

wget -N --progress=dot:giga "${ZEPHYR_SDK_URL}" -O zephyr-sdk.tar.gz && \
    mkdir -p /opt/zephyr-sdk && \
    tar -xf zephyr-sdk.tar.gz --strip 1 -C /opt/zephyr-sdk && \
    rm zephyr-sdk.tar.gz

west init -l . --mf "${ZPL_WEST_MANIFEST}"
west update
uv pip install -r ../zephyr/scripts/requirements.txt
west patch -b "${ZPL_PATCH_BASE}" -l "${ZPL_PATCH_YML}" apply
west zephyr-export
