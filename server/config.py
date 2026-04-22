# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides configuration classes for server components.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TraceConfig:
    """
    Holds configuration for trace gathering.
    """

    tcp_host: str
    tcp_port: int
    build_dir: Path = Path("build")
    tflm_model_paths: Optional[list[Path]] = None
    tvm_model_paths: Optional[list[Path]] = None
    tvm_model_metadata_paths: Optional[list[Path]] = None
    tvm_model_op_remove_prefix: Optional[re.Pattern] = None
    tvm_model_op_remove_suffix: Optional[re.Pattern] = None
