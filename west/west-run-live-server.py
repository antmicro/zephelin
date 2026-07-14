# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0


"""ZPL West extension for running live tracing server."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "server"))
from textwrap import dedent

from run_backend import run_backend, setup_parser_args
from west.commands import WestCommand


class ZplLiveServer(WestCommand):
    """
    Main class for the zpl-live-server command.
    """

    def __init__(self):
        """Init function for the zpl-live-server command."""
        super().__init__(
            "zpl-live-server",
            "Runs live capture server",
            dedent("""
                Runs live capture server.

                This command runs live tracing server to gather traces."""),
        )

    def do_add_parser(self, parser_adder, parser=None):
        if parser is None:
            parser = parser_adder.add_parser(
                self.name, help=self.help, description=self.description
            )

        parser = setup_parser_args(parser)

        return parser

    def do_run(self, args, unknown_args=None):
        run_backend(args)
