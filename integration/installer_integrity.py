#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fail-closed checks around the pinned ArtisanROM S10 OTA packaging path.

No recovery/device writes. Image checks use host tools built from pinned sources.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

ARTISAN_UPDATER_BLOB = '1c284c9122280882fed25ce6e3f40747f938051e'
ARTISAN_UPDATER_SIZE = 2362000
SPARSE_MAGIC = 0xED26FF3A
EROFS_MAGIC = 0xE0F5E1E2


def verify_updater(workspace):
    path = workspace / 'prebuilts/bootable/deprecated-ota/updater'
    data = path.read_bytes()
    digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if len(data) != ARTISAN_UPDATER_SIZE or digest != ARTISAN_UPDATER_BLOB:
        raise ValueError('Installer is not the pinned ArtisanROM S10 updater; refusing substitution')
    return {'origin': 'ArtisanROM-archive/ArtisanROM_old',
            'commit': '5638a7f66cdf8bc9dd43f087a96f7dfa4f9e6954',
            'updater_git_blob': digest, 'updater_sha256': hashlib.sha256(data).hexdigest()}


def verify_image(image):
    with image.open('rb') as stream:
        magic = stream.read(4)
    sparse = magic == struct.pack('<I', SPARSE_MAGIC)
    with tempfile.TemporaryDirectory(prefix='image-check-', dir=image.parent) as temporary:
        raw = Path(temporary) / 'raw.img' if sparse else image
        if sparse:
            subprocess.run(['simg2img', str(image), str(raw)], check=True)
        with raw.open('rb') as stream:
            stream.seek(1024)
            erofs = stream.read(4) == struct.pack('<I', EROFS_MAGIC)
        if erofs:
            # --extract without =directory verifies ALL file encodings without
            # writing an extracted filesystem (pinned fsck/main.c option 2).
            subprocess.run(['fsck.erofs', '--extract', str(raw)], check=True)
        else:
            # ext4 magic at superblock+0x38; never repair/modify a build image.
            with raw.open('rb') as stream:
                stream.seek(1024 + 0x38)
                ext4 = stream.read(2) == b'\x53\xef'
            if not ext4:
                raise ValueError('Unrecognized OS image filesystem')
            subprocess.run(['e2fsck', '-f', '-n', str(raw)], check=True)
        return {'status': 'filesystem-verified', 'filesystem': 'erofs' if erofs else 'ext4',
                'logical_bytes': raw.stat().st_size, 'sparse': sparse}


def verify_brotli(payload, original):
    """Compare the entire decompressed payload against img2sdat output, bounded RAM."""
    digest = hashlib.sha256()
    size = 0
    with original.open('rb') as expected, subprocess.Popen(
            ['brotli', '--decompress', '--stdout', str(payload)], stdout=subprocess.PIPE) as process:
        try:
            while True:
                chunk = process.stdout.read(1024 * 1024)
                if not chunk:
                    break
                if chunk != expected.read(len(chunk)):
                    raise ValueError('Brotli payload roundtrip differs from original new.dat')
                digest.update(chunk)
                size += len(chunk)
            if expected.read(1) or process.wait() != 0:
                raise ValueError('Truncated/invalid Brotli payload')
        except BaseException:
            process.kill()
            process.wait()
            raise
    return {'status': 'brotli-roundtrip-verified', 'new_dat_bytes': size,
            'new_dat_sha256': digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['updater', 'image', 'brotli'])
    parser.add_argument('path', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--original', type=Path)
    args = parser.parse_args()
    if args.action == 'updater':
        report = verify_updater(args.path)
    elif args.action == 'image':
        report = verify_image(args.path)
    else:
        if args.original is None:
            parser.error('--original is required for brotli verification')
        report = verify_brotli(args.path, args.original)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
