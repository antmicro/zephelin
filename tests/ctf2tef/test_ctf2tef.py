"""Tests features related to CTF to TEF conversion."""

import os
import sys
from pathlib import Path

import bt2

sys.path.append(str(Path.cwd() / "scripts"))
import ctf2tef
import prepare_trace

zephyr_base = os.environ.get("ZEPHYR_BASE", None)
zephyr_base = Path(zephyr_base) if zephyr_base is not None else None


def test_metadata():
    """Tests CTF metadata file."""
    with ctf2tef.prepare_dir(Path("/dev/null"), zephyr_base) as d:
        bt2.TraceCollectionMessageIterator(str(d.resolve()))


def test_ctf2tef():
    """Tests CTF to TEF conversion."""
    with ctf2tef.prepare_dir(Path("./tests/ctf2tef/trace.ctf"), zephyr_base) as d:
        ctf2tef.ctf_to_tef(
            str(d), False, prepare_trace.CUSTOM_METADATA, prepare_trace.CUSTOM_EVENTS
        )
