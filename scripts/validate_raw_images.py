#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validate intermediate RAW image payloads before TWRP ZIP packaging."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from integration.raw_images import PROOF_ROOT, sha256, verify_bundle
from integration.targets import from_marker


def main():
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} /absolute/workspace', file=sys.stderr)
        return 64
    workspace = Path(sys.argv[1]).resolve()
    marker_path = workspace / 'BEYOUD-WORKSPACE.json'
    lock_path = workspace / 'out/firmware-lock.json'
    if marker_path.is_symlink() or not marker_path.is_file():
        raise ValueError('Missing/unsafe workspace provenance marker')
    if lock_path.is_symlink() or not lock_path.is_file():
        raise ValueError('Missing/unsafe verified firmware lock')
    marker = json.loads(marker_path.read_text())
    codename, target = from_marker(marker)
    receipt_path = workspace / PROOF_ROOT / f'{codename}.json'
    result = verify_bundle(
        workspace / 'out/raw-images' / codename,
        expected_model=target['model'],
        expected_codename=codename,
        receipt=receipt_path,
        verify_hashes=True,
    )
    receipt = json.loads(receipt_path.read_text())
    if receipt.get('firmware_lock_sha256') != sha256(lock_path):
        raise ValueError('Raw image proof does not match the verified firmware lock')
    print(json.dumps(result, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        print(f'Raw image validation stopped: {exc}', file=sys.stderr)
        raise SystemExit(1)
