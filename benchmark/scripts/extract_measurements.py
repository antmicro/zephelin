#!/usr/bin/env python3

# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Script for extracting benchmark results from twister outputs.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml


def extract_benchmark_result(benchmark):
    """Extract results from a benchmark."""
    header, *values = Path(benchmark / "out.csv").read_text().splitlines()
    columns = header.strip().split(",")

    iterations = []

    for value in values:
        iterations.append(dict(zip(columns, value.strip().split(","))))

    return iterations


def extract_benchmark_ram_report(benchmark):
    """Extract a ram report from a benchmark."""
    ram_report_start = None
    lines = Path(benchmark / "build.log").read_text().splitlines()
    for i, line in enumerate(lines):
        if all((x in line for x in ["Memory region", "Used Size", "Region Size"])):
            ram_report_start = i
        if ram_report_start is not None and "Generating files from" in line:
            ram_report_end = i
            break

    parsed = dict()

    ram_report = lines[ram_report_start:ram_report_end]
    for line in ram_report[1:]:
        words = line.split()
        region, *words = words
        sizes = []

        for word, next_word in zip(words, words[1:]):
            if not word.isdecimal():
                continue

            multiplier = {
                "B": 1,
                "KB": 2**10,
                "MB": 2**20,
                "GB": 2**30,
            }.get(next_word, 1)

            sizes.append(int(word) * multiplier)

        parsed[region.rstrip(":")] = {
            "used": sizes[0],
            "total": sizes[1],
        }

    return parsed


def extract_results(path: Path):
    """Extract benchmark results from twister outputs."""
    boards = [p for p in path.iterdir() if p.is_dir()]

    board_benchmarks = {board: list(board.glob("*/*/benchmark/*")) for board in boards}

    results = dict()

    for board, benchmarks in board_benchmarks.items():
        print(f"Board: {board.name}")
        board_results = dict()
        for benchmark in benchmarks:
            print(f"  Benchmark: {benchmark.name}")

            iterations = extract_benchmark_result(benchmark)
            ram_report = extract_benchmark_ram_report(benchmark)

            board_results[benchmark.name] = {
                "iterations": iterations,
                "ram_report": ram_report,
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
        return dict()
    commits_ids = dict()
    for path in paths:
        path = Path(path)
        raw = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
        )
        commits_ids[path.resolve().name] = raw.decode().strip()

    return commits_ids


def extract_configs(path: str | Path):
    """Extract used config files."""
    path = Path(path)
    with (path / "sample.yaml").open() as f:
        sample = yaml.safe_load(f)

    all_conf_files = set(["prj.conf"])
    benchmark_conf = dict()
    benchmark_names = dict()

    pattern_conf = re.compile("[;=](.*?\.conf)")
    pattern_names = re.compile("(CONFIG_ZPL_BENCHMARK_RUN_.*?)=[yn]")

    for benchmark, config in sample["tests"].items():
        conf_files = pattern_conf.findall(config.get("extra_args", ""))
        all_conf_files.update(conf_files)
        benchmark_conf[benchmark] = conf_files
        benchmark_names[benchmark] = (
            pattern_names.search(config.get("extra_configs", [])[0])
            .group(1)
            .partition("CONFIG_")[-1]
        )

    all_conf = {p: (path / p).read_text() for p in all_conf_files}

    configs = {
        "benchmarks": {
            "configs": benchmark_conf,
            "names": benchmark_names,
        },
        "contents": all_conf,
    }

    return configs


def extract_benchmarks(path: str | Path):
    """Extract benchmark descriptions."""
    path = Path(path)
    conf = (path / "Kconfig").read_text()
    pattern = re.compile(
        """config\s(ZPL_BENCHMARK_RUN_.*?)\n
        \s*bool\s(.*)\n
        \s*help\s(.*)""",
        flags=re.M | re.X,
    )

    name_map = {v: k for k, v in configs["benchmarks"]["names"].items()}
    print(name_map)

    benchmarks = dict()
    for name, prompt, desc in pattern.findall(conf):
        prompt = prompt.strip('"')
        benchmarks[name] = f"{prompt.strip()}\n\n{desc.strip()}\n"

    return benchmarks


if __name__ == "__main__":
    path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    results = extract_results(path)
    commits = extract_commit_ids([".", "../zephyr"])
    configs = extract_configs("./benchmark")
    benchmarks = extract_benchmarks("./benchmark")

    results = {
        "results": results,
        "commits": commits,
        "configs": configs,
        "benchmarks": benchmarks,
    }

    out_path.write_text(json.dumps(results, indent=2))
