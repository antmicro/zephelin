# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0
#
# A script that is meant to be sourced.
# Exports Zephyr version related variables into the shell.


ZPL_DEFAULT_ZEPHYR_VERSION=v4.3.0

_zpl_request="${1:-${ZEPHYR_VERSION:-}}"

_zpl_root="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"

# Retrieve the version of Zephyr from the west-X.yml file name
_zpl_manifest="$(west config manifest.file 2>/dev/null || true)"
case "$_zpl_manifest" in
    west.yml)             _zephyr_version="$ZPL_DEFAULT_ZEPHYR_VERSION" ;;   # If plain west.yml is the manifest use default
    manifests/west-*.yml) _zephyr_version="${_zpl_manifest#manifests/west-}" # If specific west-X.yml extract X
                          _zephyr_version="${_zephyr_version%.yml}" ;;
    *)                    _zephyr_version="" ;;                              # Otherwaise leave empty
esac

if [ -n "$_zephyr_version" ] && [ -n "$_zpl_request" ] && [ "$_zpl_request" != "$_zephyr_version" ]; then
    echo "note: this workspace is set up for Zephyr $_zephyr_version, ignoring the request for $_zpl_request." >&2
    echo "      To move it over, run: ./scripts/switch_zephyr_version.sh $_zpl_request" >&2
fi

export ZPL_ZEPHYR_VERSION="${_zephyr_version:-${_zpl_request:-$ZPL_DEFAULT_ZEPHYR_VERSION}}"

if [ ! -f "${_zpl_root}/zephyr-versions/${ZPL_ZEPHYR_VERSION}.env" ]; then
    echo "error: unknown Zephyr version '${ZPL_ZEPHYR_VERSION}'; supported versions are:" >&2
    ls "${_zpl_root}/zephyr-versions/" >&2
    return 1
fi

set -a
. "${_zpl_root}/zephyr-versions/${ZPL_ZEPHYR_VERSION}.env"
set +a

export ZPL_WEST_MANIFEST="manifests/west-${ZPL_ZEPHYR_VERSION}.yml"
export ZPL_PATCH_BASE="zephyr/patches/${ZPL_ZEPHYR_VERSION}"
export ZPL_PATCH_YML="zephyr/patches/${ZPL_ZEPHYR_VERSION}.yml"

unset _zpl_root _zpl_manifest _zephyr_version _zpl_request
