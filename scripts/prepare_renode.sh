#!/bin/sh

# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

if [ -d renode_portable ] ; then
  echo "Renode already downloaded."
else
  echo "Downloading Renode..."
  curl https://builds.renode.io/renode-1.16.0+20250929gitc16006c94.linux-portable-dotnet.tar.gz -o renode-pkg.tar.gz
  tar -xf renode-pkg.tar.gz
  rm -f renode-pkg.tar.gz
  mv -f renode_*portable renode_portable
fi

echo "Preparing environment..."
export PYRENODE_BIN=$(realpath renode_portable/renode)
export PYRENODE_RUNTIME=coreclr
export PATH=$PATH:$(realpath renode_portable/)
