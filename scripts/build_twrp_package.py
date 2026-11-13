#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build an experimental TWRP-installable ROM ZIP from the verified S10 target."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from integration.twrp_package import main


if __name__ == '__main__':
    raise SystemExit(main())
