#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validate the final TWRP-installable X-NovaOS ROM ZIP and its private proof."""
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from integration.twrp_package import verify_workspace


def main():
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} /absolute/workspace', file=sys.stderr)
        return 64
    try:
        result = verify_workspace(Path(sys.argv[1]))
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f'TWRP ROM ZIP validation stopped: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
