#!/bin/bash

# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

# Move an existing west workspace to another supported Zephyr version.
#
# Example usage: ./scripts/switch_zephyr_version.sh v4.4.1

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "usage: $0 <zephyr-version>" >&2
    exit 1
fi

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ ! -f "zephyr-versions/$1.env" ]; then
    echo "error: unknown Zephyr version '$1'; expected one of:" >&2
    ls zephyr-versions/ | sed 's/\.env$//;s/^/  /' >&2
    exit 1
fi

source ./scripts/zephyr_version.sh ""
echo "Removing Zephyr ${ZPL_ZEPHYR_VERSION} patches..."
west patch -b "$ZPL_PATCH_BASE" -l "$ZPL_PATCH_YML" clean

west config manifest.file "manifests/west-$1.yml"
west update

source ./scripts/zephyr_version.sh "$1"
west patch -b "$ZPL_PATCH_BASE" -l "$ZPL_PATCH_YML" apply

echo
echo "Workspace is now on Zephyr ${ZPL_ZEPHYR_VERSION}."
echo "The Zephyr SDK is NOT switched; ${ZPL_ZEPHYR_VERSION} expects SDK ${ZEPHYR_SDK_VERSION}."
