# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Helper GDB functions to use in Robot scripts."""

import re
import subprocess


def gdb_dump_trace_data(script, elf):
    """Run a GDB subprocess with a given script."""
    # skip the first character, which is the '@' symbol
    elf = elf[1:]
    cmd = f"gdb-multiarch -batch -x {script} {elf}".split(" ")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    (output, _) = proc.communicate()
    exit_code = proc.wait()

    if exit_code != 0:
        raise Exception("Failed to dump trace data: {}!".format(output))


def gdb_verify_trace_data(pattern):
    """Verify GDB dump against a pattern."""
    with open("out.bin") as f:
        out = f.read()

    matches = re.findall(pattern, out)

    if len(matches) == 0:
        raise Exception(f"No pattern {pattern} matched!")
