#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compatibility CLI for building an experimental TWRP ROM ZIP from RAW images."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from integration.twrp_zip_builder import main


if __name__ == '__main__':
    raise SystemExit(main())
