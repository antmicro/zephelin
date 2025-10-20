#!/bin/bash

# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

set -xeuo pipefail

west init -l .
west update
west patch apply
west zephyr-export
west packages pip --install --ignore-venv-check

SDK_INSTALL_ARGS=""
if [[ ! -z "${ZEPHYR_SDK_VERSION:-}" ]]; then
  SDK_INSTALL_ARGS="--version ${ZEPHYR_SDK_VERSION}"
fi

if [[ -z "${ZEPHYR_SDK_SKIP_INSTALLATION:-}" ]]; then
  west sdk install $SDK_INSTALL_ARGS
fi
