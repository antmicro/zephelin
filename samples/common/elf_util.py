# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides Robot Framework keywords for analyzing ELF files.
"""

from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection


def elf_symbol_to_address(elf_path, symbol):
    """
    Gets address of the symbol from the ELF file.
    """
    if elf_path[0] == "@":
        elf_path = elf_path[1:]

    with open(elf_path, "rb") as f:
        elf = ELFFile(f)
        for section in elf.iter_sections():
            if isinstance(section, SymbolTableSection):
                for s in section.iter_symbols():
                    if (
                        s["st_shndx"] != "SHN_UNDEF"
                        and s.name
                        and not s.name.startswith("$")
                        and s.name == symbol
                    ):
                        return s["st_value"]
