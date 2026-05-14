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
    bench_names = results["configs"]["benchmarks"]["names"]
    for board, board_benchmarks in sorted(results["results"].items()):
        print(board)
        benchmarks[board] = tabulate(
            [
                [
                    (
                        f"[{k} ({bench_names[k].partition('ZPL_BENCHMARK_RUN_')[-1].lower()})]"
                        f"(#{bench_names[k].lower()})"
                    ),
                    v["cycles_mean"],
                    v["ram_report"]["RAM"]["used"],
                    v["ram_report"]["FLASH"]["used"],
                    ", ".join(
                        (
                            f"[{r}](#{r.replace('.', '-').replace('_', '-')})"
                            for r in results["configs"]["benchmarks"]["configs"][k]
                        )
                    ),
                ]
                for k, v in sorted(board_benchmarks.items())
            ],
            headers=["Benchmark", "Cycles", "FLASH [B]", "RAM [B]", "Configs"],
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
        configs=results["configs"]["contents"],
        benchmark_desc=results["benchmarks"],
    )


if __name__ == "__main__":
    path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    results = json.loads(path.read_text())
    out_path.write_text(generate(results))
