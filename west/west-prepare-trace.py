# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
ZPL West extension for preparing captured trace,
e.g. converting it to TEF and extending with additional data.
"""

import sys
from pathlib import Path
from subprocess import run
from textwrap import dedent

from west.commands import WestCommand
from west.util import west_topdir

# Extend PYTHONPATH with ZPL scripts directory
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from prepare_trace import prepare, setup_parser


class ZplPrepareTrace(WestCommand):
    """
    Main class for the zpl-prepare-trace command.
    """

    def __init__(self):
        """
        Defines name and description of zpl-prepare-trace command.
        """
        super().__init__(
            "zpl-prepare-trace",
            "Prepares trace for the visualization",
            dedent("""
                Prepares trace for the visualization.

                This command converts trace from CTF to TEF and extends it with metadata, like:
                * model info (inputs, outputs, layers details etc.),
                * additional symbols associated with memory regions,
                * thread names and their IDs.

                It requires babeltrace2 to work,
                and optionally ai_edge_litert to extract metadata from LiteRT models.
                """),
        )

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name, help=self.help, description=self.description)

        parser = setup_parser(parser)

        return parser

    def do_run(self, args, unknown_args):
        self.inf("Running ram_report")
        # Run ram_report, capture all output
        # as results are also saved to ram.json in build dir
        ret = run(["west", "build", "-t", "ram_report"], capture_output=True)
        if ret.returncode != 0:
            self.err("Building ram_report failed")
            self.dbg("with errors:", ret.stderr)

        if not args.build_dir:
            self.dbg("Trying to find build dir")
            # Extend PYTHONPATH with Zephyr West scripts directory
            # and import helper functions
            topdir = west_topdir()
            sys.path.insert(
                1, str((Path(topdir) / "zephyr" / "scripts" / "west_commands").resolve())
            )
            from build_helpers import find_build_dir

            build_dir = find_build_dir(None)
            if build_dir is not None:
                args.build_dir = Path(build_dir)

        self.inf("Preparing trace")
        prepare(args)
