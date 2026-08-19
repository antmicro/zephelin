#!/bin/bash

# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

source "$(dirname "${BASH_SOURCE[0]:-$0}")/zephyr_version.sh" "" || return 1 2>/dev/null || exit 1

if [ -d renode_portable ] ; then
  echo "Renode already downloaded."
else
  echo "Downloading Renode ${ZPL_RENODE_PACKAGE}..."
  curl "https://builds.renode.io/${ZPL_RENODE_PACKAGE}" -o renode-pkg.tar.gz
  tar -xf renode-pkg.tar.gz
  rm -f renode-pkg.tar.gz
  mv -f renode_*portable renode_portable
fi

echo "Preparing environment..."
export PYRENODE_BIN=$(realpath renode_portable/renode)
export PYRENODE_RUNTIME=coreclr
export PATH=$PATH:$(realpath renode_portable/)
