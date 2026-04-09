#!/usr/bin/env python3

# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Script for generating reports from benchmark results.
"""

import json
import sys
from pathlib import Path

import jinja2
from tabulate import tabulate

template_path = Path(__file__).parent / "template.md.jinja2"
template = jinja2.Template(template_path.read_text())

tablefmt = "github"


def generate(results: dict):
    """Generate report from benchmark results."""
    benchmarks = {}
    for board, board_benchmarks in sorted(results["results"].items()):
        print(board)
        benchmarks[board] = tabulate(
            [[k, v["cycles_mean"]] for k, v in sorted(board_benchmarks.items())],
            headers=["Benchmark", "Cycles"],
            tablefmt=tablefmt,
        )

    commits = tabulate(
        results["commits"].items(),
        headers=["Project", "Commit"],
        tablefmt=tablefmt,
    )

    return template.render(
        benchmarks=benchmarks,
        commits=commits,
    )


if __name__ == "__main__":
    path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    results = json.loads(path.read_text())
    out_path.write_text(generate(results))
