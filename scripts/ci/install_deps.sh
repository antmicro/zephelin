#!/bin/bash

# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

set -xeuo pipefail

export RENODE_VERSION="renode-1.16.0+20250929gitc16006c94.linux-portable-dotnet.tar.gz"

# install deps with apt
sudo apt update -qq
sudo apt install -yqq --no-install-recommends gdb-multiarch mono-complete \
  ccache dfu-util device-tree-compiler wget python3-dev python3-venv python3-tk \
  xz-utils file make gcc gcc-multilib g++-multilib libsdl2-dev libmagic1 \
  xxd git-lfs swig libelf-dev libdw-dev python3-packaging \
  libgtk2.0-0 screen uml-utilities libc6-dev libicu-dev \
  python3 python3-pip git cmake ninja-build gperf unzip qemu-system-arm

pip install --break-system-packages uv
uv venv -p 3.11
source .venv/bin/activate

uv pip install --upgrade pip

# install deps with pip
uv pip install -r requirements.txt

# install recent flatbuffers-compiler
FLATC_URL=https://github.com/google/flatbuffers/releases/download/v25.2.10/Linux.flatc.binary.g++-13.zip
wget ${FLATC_URL} -O flatc.zip
sudo unzip flatc.zip -d /usr/bin
rm flatc.zip

# install Renode
wget -q "https://dl.antmicro.com/projects/renode/builds/${RENODE_VERSION}" -O renode.tar.gz
rm -rf /opt/renode
mkdir /opt/renode
tar -xf  renode.tar.gz -C /opt/renode --strip-components=1
rm renode.tar.gz
