# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides configuration classes for server components.
"""

from dataclasses import dataclass


@dataclass
class TraceConfig:
    """
    Holds configuration for trace gathering.
    """

    tcp_host: str
    tcp_port: int
