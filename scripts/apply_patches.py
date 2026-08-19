# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Script for applying patches as commits."""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml


def _confirm(prompt):
    """Ask the user to confirm a destructive action."""
    if not sys.stdin.isatty():
        return False
    try:
        return input(f"{prompt} [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def apply_patches(
    map_path="zephyr/patch_map.yml",
    source_root="zephyr/patches",
    target_root="../",
    assume_yes=False,
):
    """Apply patches as commits."""
    patch_map_path = Path(map_path)
    patch_map: dict[str, str] = yaml.safe_load(patch_map_path.read_text())

    source_root = Path(source_root)
    target_root = Path(target_root)

    if not assume_yes and not _confirm(
        "Applying patches resets the target repositories to manifest-rev and "
        "may discard some changes. Continue?"
    ):
        print("Aborted. Re-run with -y/--yes to proceed.", file=sys.stderr)
        sys.exit(1)

    for source, target in patch_map.items():
        repo = str((target_root / target).resolve())
        patches = sorted(list((source_root / source).glob("*.patch")))
        str_patches = [str(x.resolve()) for x in patches]

        if not str_patches:
            print(f"No patches found for '{source}'")
            continue

        subprocess.run(
            ["git", "am", "--abort"],
            cwd=repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        subprocess.run(
            ["git", "reset", "--hard", "manifest-rev"],
            check=True,
            cwd=repo,
            stderr=sys.stderr,
            stdout=sys.stdout,
        )

        try:
            subprocess.run(
                ["git", "am", "--committer-date-is-author-date", *str_patches],
                check=True,
                cwd=repo,
                stderr=sys.stderr,
                stdout=sys.stdout,
            )
        except subprocess.CalledProcessError:
            subprocess.run(["git", "am", "--abort"], cwd=repo, check=False)
            print(f"Failed to apply patches for '{target}'", file=sys.stderr)
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompts before resetting repos to manifest-rev.",
    )
    args = parser.parse_args()
    apply_patches(assume_yes=args.yes)
