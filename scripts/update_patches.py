# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Script for converting commits into patches."""

import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


def update_patches(
    map_path="zephyr/patch_map.yml",
    source_root="zephyr/patches",
    target_root="../",
    patches_yml_path="zephyr/patches.yml",
):
    """Update patches from commits."""
    patch_map_path = Path(map_path)
    patch_map: dict[str, str] = yaml.safe_load(patch_map_path.read_text())

    source_root = Path(source_root)
    target_root = Path(target_root)

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
    update_patches()
