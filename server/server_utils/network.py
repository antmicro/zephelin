# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
A set of basic networking utilities.
"""

import socketserver


def find_free_port() -> str:
    """
    Finds a port number on localhost, that is not busy. Please note, that this
    function does not 'reserve' the port number in any way - it returns a
    port that is free at the moment of calling, there is no guarantee the port
    will remain free.

    Returns
    -------
    str
        Port number.
    """
    with socketserver.TCPServer(("localhost", 0), None) as s:
        return s.server_address[1]
