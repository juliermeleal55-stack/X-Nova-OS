#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build a separate experimental RAW installer from completed S10 build images.

Does not download firmware, build a ROM, sign APKs or alter the existing pipeline.
Requires host filesystem tools on PATH. Output is NOT an approved release.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from integration.installer_integrity import SPARSE_MAGIC, verify_image

ORDER = ('system', 'vendor', 'product', 'odm', 'prism', 'optics', 'system_ext', 'dtbo', 'boot')
REQUIRED = {'system', 'vendor', 'product', 'dtbo', 'boot'}


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def build(images, output, device_base='/dev/block/by-name'):
    if not re.fullmatch(r'/dev/block/[A-Za-z0-9_./-]+', device_base) or '..' in device_base:
        raise ValueError('Unsafe device base')
    available = {p.stem for p in images.glob('*.img')}
    if not REQUIRED <= available or available - set(ORDER):
        raise ValueError('Missing required or unsupported image role (no recovery/data/EFS writes)')
    if output.exists():
        raise ValueError('Refusing to replace an existing package')
    records = []
    created = False
    try:
        with tempfile.TemporaryDirectory(prefix='xnova-raw-host-', dir=output.parent) as temporary:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
                created = True
                for name in ORDER:
                    if name not in available:
                        continue
                    source = images / (name + '.img')
                    if source.is_symlink() or not source.is_file():
                        raise ValueError('Unsafe image input')
                    with source.open('rb') as stream:
                        header = stream.read(32)
                    sparse = header[:4] == struct.pack('<I', SPARSE_MAGIC)
                    raw = source
                    if sparse:
                        if name in {'boot', 'dtbo'}:
                            raise ValueError('Boot image must be raw')
                        raw = Path(temporary) / (name + '.img')
                        subprocess.run(['simg2img', str(source), str(raw)], check=True)
                    if name == 'boot':
                        if not header.startswith(b'ANDROID!'):
                            raise ValueError('Invalid Android boot image')
                    elif name == 'dtbo':
                        if header[:4] != bytes.fromhex('d7b7ab1e'):
                            raise ValueError('Invalid DTBO image')
                    else:
                        verify_image(raw)  # Real fsck, not a header-only pass.
                    size = raw.stat().st_size
                    if size <= 0 or size >= 2**53:
                        raise ValueError('Invalid/unsupported image byte count')
                    record = dict(name=name, bytes=size, sha256=sha256(raw))
                    records.append(record)
                    archive.write(raw, f'images/{name}.img')
                    if raw != source:
                        raw.unlink()
                manifest = ''.join(f"{r['name']}\t{r['bytes']}\t{r['sha256']}\n" for r in records)
                archive.writestr('installer/manifest.tsv', manifest)
                archive.writestr('installer/device-base', device_base + '\n')
                guard = '#!/sbin/sh\n' + (ROOT / 'integration/recovery_layout_check.sh').read_text() + '\n'
                guard += ''.join(f"check_partition {r['name']} {r['bytes']} || failures=1\n" for r in records)
                guard += 'exit "$failures"\n'
                archive.writestr('installer/layout-check.sh', guard)
                archive.write(ROOT / 'integration/new_installer/engine.sh', 'installer/engine.sh')
                info = zipfile.ZipInfo('META-INF/com/google/android/update-binary')
                info.external_attr = (0o100755 << 16)
                archive.writestr(info, (ROOT / 'integration/new_installer/update-binary.sh').read_bytes())
                archive.writestr('REQUIRED-IMAGE-SIZES.json', json.dumps({
                    'model': 'SM-G973F', 'installer': 'xnova-raw-v1-experimental',
                    'image_size_bytes': {r['name']: r['bytes'] for r in records}}, indent=2))
                archive.writestr('WARNING.txt', 'EXPERIMENTAL INSTALLER CANDIDATE: not tested on hardware, not release-approved.\nNon-atomic writes; interruption may leave an unbootable device. Requires free userdata space for ALL staged images.\nNo format, repartition, automatic mount, Edify, Brotli, img2sdat or block_image_update.\nKeep backups and a stock restore procedure. Package is not outer-signed by this prototype builder.\n')
                archive.writestr('installer/provenance.json', json.dumps({'model': 'SM-G973F', 'images': records,
                    'credits': 'X-Nova OS; images retain Artisan/Extreme/UN1CA provenance and licenses. Capacity guard GPL-3.0-or-later.'}, indent=2))
                # Last entry uses ZIP64 local header even for the tiny probe.
                with archive.open('installer/zip64-probe.txt', 'w', force_zip64=True) as probe:
                    probe.write(b'XNOVA_RAW_V1\n')
        with zipfile.ZipFile(output) as archive:
            if archive.testzip() is not None:
                raise ValueError('Generated package failed CRC')
        return records
    except BaseException:
        if created:
            output.unlink(missing_ok=True)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--device-base', default='/dev/block/by-name')
    parser.add_argument('--experimental', action='store_true', help='Acknowledge candidate, not hardware validated or approved for release')
    args = parser.parse_args()
    if not args.experimental:
        parser.error('--experimental is required; no package is release-approved')
    build(args.images, args.output, args.device_base)
    print(json.dumps({'package': str(args.output), 'sha256': sha256(args.output), 'status': 'experimental-not-approved'}))
