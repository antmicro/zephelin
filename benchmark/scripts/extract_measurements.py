#!/usr/bin/env python3

# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Script for extracting benchmark results from twister outputs.
"""

import json
import subprocess
import sys
from pathlib import Path


def extract_results(path: Path):
    """Extract benchmark results from twister outputs."""
    boards = [p for p in path.iterdir() if p.is_dir()]

    board_benchmarks = {board: list(board.glob("*/*/benchmark/*")) for board in boards}

    results = {}

    for board, benchmarks in board_benchmarks.items():
        print(f"Board: {board.name}")
        board_results = {}
        for benchmark in benchmarks:
            print(f"  Benchmark: {benchmark.name}")

            header, *values = (benchmark / "out.csv").read_text().splitlines()
            columns = header.strip().split(",")

            iterations = []

            for value in values:
                iterations.append(dict(zip(columns, value.strip().split(","))))

            board_results[benchmark.name] = {
                "iterations": iterations,
                "cycles_mean": int(sum((float(x["cycles"]) for x in iterations)) / len(iterations)),
            }
        results[board.name] = board_results

    return results


def extract_commit_ids(paths: list[Path | str]):
    """Extract commit ids from paths."""
    try:
        subprocess.check_output(["git", "--version"])
    except FileNotFoundError as e:
        print(f"Skipping commit ids: {e}")
        return {}
    commits_ids = {}
    for path in paths:
        path = Path(path)
        raw = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
        )
        commits_ids[path.resolve().name] = raw.decode().strip()

    return commits_ids


if __name__ == "__main__":
    path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    results = {"results": extract_results(path), "commits": extract_commit_ids([".", "../zephyr"])}

    out_path.write_text(json.dumps(results, indent=2))
