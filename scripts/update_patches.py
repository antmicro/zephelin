# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Script for converting commits into patches."""

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


def update_patches(
    source_root,
    patches_yml_path,
    map_path="zephyr/patch_map.yml",
    target_root="../",
):
    """Regenerate one Zephyr version's patch set from the module checkouts."""
    patch_map_path = Path(map_path)
    patch_map: dict[str, str] = yaml.safe_load(patch_map_path.read_text())

    source_root = Path(source_root)
    target_root = Path(target_root)

    if not source_root.is_dir():
        sys.exit(f"error: patch base '{source_root}' does not exist.")

    for source, target in patch_map.items():
        shutil.rmtree(source_root / source, ignore_errors=True)
        subprocess.run(
            [
                "git",
                "format-patch",
                "-o",
                str((source_root / source).resolve()),
                "manifest-rev",
            ],
            check=True,
            cwd=str((target_root / target).resolve()),
            stderr=sys.stderr,
            stdout=sys.stdout,
        )

    patches_yml = []

    for source in patch_map.keys():
        for patch in sorted(list((source_root / source).glob("*.patch"))):
            path = str(Path(source) / patch.name)
            sha256sum = (
                subprocess.check_output(["sha256sum", str(patch)]).decode().strip().split()[0]
            )
            module = source

            lines = patch.read_text().splitlines()
            author_str = lines[1].removeprefix("From:").strip()
            author, email = re.match(r"(.+)\<(.+?)\>", author_str).groups()

            date_str = lines[2].removeprefix("Date:").strip()

            date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d")

            patches_yml.append({
                "path": path,
                "sha256sum": sha256sum,
                "module": module,
                "author": author.strip(),
                "email": email,
                "date": date,
            })

    patches_str = yaml.dump({"patches": patches_yml})

    prefix = """# yamllint disable rule:line-length"""

    patches_yml_path = Path(patches_yml_path)
    patches_yml_path.write_text(f"{prefix}\n{patches_str}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument(
        "-s",
        "--source-root",
        default=None,
        help="Patch base to rewrite.",
    )
    args = parser.parse_args()

    source_root = args.source_root or os.environ.get("ZPL_PATCH_BASE")
    patches_yml = os.environ.get("ZPL_PATCH_YML")
    if not source_root or not patches_yml:
        sys.exit("error: no patch set selected. Run `source ./scripts/zephyr_version.sh` first.")

    update_patches(source_root, patches_yml)
