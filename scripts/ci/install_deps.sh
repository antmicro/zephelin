#!/bin/bash

# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

set -xeuo pipefail

if [ -z "${RENODE_VERSION:-}" ]; then
	echo "RENODE_VERSION is not set!"
	exit 1
fi

# install deps with apt
apt update -qq
apt install -yqq xxd gdb-multiarch

# install deps with pip
pip install -r requirements.txt

# install Renode
wget -q "https://dl.antmicro.com/projects/renode/builds/${RENODE_VERSION}" -O renode.deb
dpkg -i renode.deb
rm renode.deb
