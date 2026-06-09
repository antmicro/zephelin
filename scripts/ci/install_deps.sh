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
sudo apt update -qq
sudo apt install -yqq --no-install-recommends gdb-multiarch mono-complete \
  ccache dfu-util device-tree-compiler wget python3-dev python3-venv python3-tk \
  xz-utils file make gcc gcc-multilib g++-multilib libsdl2-dev libmagic1 \
  xxd git-lfs swig libelf-dev libdw-dev python3-packaging \
  policykit-1 libgtk2.0-0 screen uml-utilities gtk-sharp2 libc6-dev libicu-dev \
  python3 python3-pip git cmake ninja-build gperf unzip

pip3 install --upgrade pip

# install deps with pip
pip3 install -r requirements.txt

# install recent flatbuffers-compiler
FLATC_URL=https://github.com/google/flatbuffers/releases/download/v25.2.10/Linux.flatc.binary.g++-13.zip
wget ${FLATC_URL} -O flatc.zip
sudo unzip flatc.zip -d /usr/bin
rm flatc.zip

# install Renode
wget -q "https://dl.antmicro.com/projects/renode/builds/${RENODE_VERSION}" -O renode.deb
sudo dpkg -i renode.deb
rm renode.deb
