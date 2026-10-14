# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides Robot Framework keywords for accessing Zephyr build artifacts.
"""

import os
from pathlib import Path

import yaml


class ZephyrBuildDir:
    """
    Provides methods for accessing artifacts from Zephyr sysbuild domains.
    """

    def __init__(self):
        """
        Creates ZephyrBuildDir.
        """
        self.domains_file = Path(os.getcwd()) / "domains.yaml"

        if not self.domains_file.exists():
            raise FileNotFoundError(f"Domains file does not exist: {self.domains_file}")

        with self.domains_file.open() as file:
            domains_data = yaml.safe_load(file)

        self.domains = {
            domain["name"]: Path(domain["build_dir"]) for domain in domains_data["domains"]
        }

    def get_zephyr_image_elf(self, domain: str) -> str:
        """
        Gets the ELF file path for the specified Zephyr sysbuild domain.

        Parameters
        ----------
        domain : str
            Name of the sysbuild domain.

        Returns
        -------
        str
            Absolute path to the ELF file.

        Raises
        ------
        ValueError
            Raised when the domain is unknown or has no ELF configured.
        FileNotFoundError
            Raised when the ELF file does not exist.
        """
        if domain not in self.domains:
            raise ValueError(f"Unknown Zephyr domain: {domain}")

        build_dir = self.domains[domain]

        if not build_dir.is_absolute():
            build_dir = self.domains_file.parent / build_dir

        runners_file = build_dir / "zephyr" / "runners.yaml"

        with runners_file.open() as file:
            runners_data = yaml.safe_load(file)

        elf_file = runners_data["config"].get("elf_file")

        if not elf_file:
            raise ValueError(f"No ELF configured for domain: {domain}")

        elf_path = Path(elf_file)

        if not elf_path.is_absolute():
            elf_path = runners_file.parent / elf_path

        elf_path = elf_path.resolve()

        if not elf_path.is_file():
            raise FileNotFoundError(f"ELF file not found: {elf_path}")

        return str(elf_path)
