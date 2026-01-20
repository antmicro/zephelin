# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Script for applying patches as commits."""

import subprocess
import sys
from pathlib import Path

import yaml


def apply_patches(
    map_path="zephyr/patch_map.yml",
    source_root="zephyr/patches",
    target_root="../",
):
    """Apply patches as commits."""
    patch_map_path = Path(map_path)
    patch_map: dict[str, str] = yaml.safe_load(patch_map_path.read_text())

    source_root = Path(source_root)
    target_root = Path(target_root)

    for source, target in patch_map.items():
        patches = sorted(list((source_root / source).glob("*.patch")))
        str_patches = [str(x.resolve()) for x in patches]

        subprocess.run(
            ["git", "am", "--committer-date-is-author-date", *str_patches],
            check=True,
            cwd=str((target_root / target).resolve()),
            stderr=sys.stderr,
            stdout=sys.stdout,
        )


if __name__ == "__main__":
    apply_patches()
