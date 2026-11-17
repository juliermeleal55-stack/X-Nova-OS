#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build and structurally verify an experimental TWRP-installable ROM ZIP.

The ZIP carries expanded RAW partition images and its own update-binary script.
It neither bundles nor modifies recovery. It is not hardware-validated or
release-approved. Tests never write to a block device.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from integration.installer_integrity import SPARSE_MAGIC, verify_image
from integration.raw_images import (
    DT_TABLE_MAGIC,
    FILESYSTEM_ORDER,
    IMAGE_ORDER,
    KERNEL_ORDER,
    REQUIRED_IMAGES,
    verify_bundle as verify_raw_bundle,
)
from integration.targets import TWRP_ROM_TARGETS
from integration.package_inputs import (
    EXTREME_REPARTITIONER_PARTITIONS,
    EXTREME_STRUCTURE_BOOT_COMPONENTS,
    EXTREME_STRUCTURE_PARTITIONS,
    EXTREME_STRUCTURE_PAYLOAD_FORMAT,
    EXTREME_STRUCTURE_PAYLOAD_FORMAT_SOURCE,
    EXTREME_STRUCTURE_REFERENCE_SCOPE,
)

ORDER = IMAGE_ORDER
REQUIRED = REQUIRED_IMAGES
FILESYSTEM_IMAGES = set(FILESYSTEM_ORDER)
KERNEL_IMAGES = set(KERNEL_ORDER)
UPDATE_BINARY = 'META-INF/com/google/android/update-binary'
DEVICE_BASE_DEFAULT = '/dev/block/by-name'
LICENSE_FILE = ROOT / 'integration/onerom/upstream/LICENSE'
LICENSE_ENTRY = 'LICENSES/GPL-3.0-or-later.txt'
CREDITS_ENTRY = 'CREDITS/OneROM-S10.md'
TARGET_MODEL_TOKEN = b'@@TARGET_MODEL@@'


def _update_binary(model):
    if not any(known_model == model for _codename, known_model in TWRP_ROM_TARGETS):
        raise ValueError('Unsupported exact TWRP model assertion')
    path = ROOT / 'integration/new_installer/update-binary.sh'
    if path.is_symlink() or not path.is_file():
        raise ValueError('Pinned TWRP update-binary template is missing/unsafe')
    template = path.read_bytes()
    if template.count(TARGET_MODEL_TOKEN) != 1:
        raise ValueError('TWRP update-binary template must contain one exact target-model token')
    return template.replace(TARGET_MODEL_TOKEN, model.encode('ascii'))


def _credits_file():
    candidates = (
        ROOT / 'reference/onerom-upstream/CREDITS.md',
        ROOT / 'reference/onerom-port-candidates/CREDITS.md',
    )
    for path in candidates:
        if path.is_symlink():
            raise ValueError('Retained OneROM credits file is unsafe')
        if path.is_file():
            return path
    raise ValueError('Retained OneROM credits/provenance file is missing')


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_stream(stream):
    digest = hashlib.sha256()
    size = 0
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(chunk)
        size += len(chunk)
    return size, digest.hexdigest()


def _source_manifest(filename):
    path = ROOT / 'manifests' / filename
    if path.is_symlink() or not path.is_file():
        return None
    data = json.loads(path.read_text())
    return {key: data.get(key) for key in ('repository', 'commit', 'license') if data.get(key) is not None}


def _provenance(records, raw_receipt=None, *, model='SM-G973F', codename='beyond1lte'):
    receipt = None
    receipt_path = None
    if raw_receipt is not None:
        receipt_path = Path(raw_receipt)
        if receipt_path.is_symlink() or not receipt_path.is_file():
            raise ValueError('Missing/unsafe raw image proof for package provenance')
        receipt = json.loads(receipt_path.read_text())
    source_manifests = {
        'artisan': _source_manifest('artisan-s10-files.json'),
        'onerom': _source_manifest('onerom.json'),
    }
    if receipt is not None and any(not value for value in source_manifests.values()):
        raise ValueError('Pinned Artisan/OneROM source manifests are required in the ROM ZIP')
    if (codename, model) not in TWRP_ROM_TARGETS:
        raise ValueError('TWRP ZIP provenance target is not an approved exact Exynos model')
    return {
        'model': model,
        'codename': codename,
        'recovery_protocol': 'TWRP Android update-binary interface',
        'recovery_included': False,
        'recovery_modified': False,
        'hardware_validated': False,
        'signature_status': 'unsigned-test-package',
        'firmware_lock_sha256': receipt.get('firmware_lock_sha256') if receipt else None,
        'raw_image_proof_sha256': sha256(receipt_path) if receipt_path else None,
        'build_identity': receipt.get('build') if receipt else None,
        'source_manifests': source_manifests,
        'credits': [
            'ArtisanROM: S10/Exynos build foundation; retain upstream attribution.',
            'OneROM: pinned target and Exynos adaptation; retain its GPL notices and per-file credits.',
            'ExtremeROM and UN1CA: upstream framework/tooling references; preserve their respective notices.',
            'Samsung and donor-firmware authors: proprietary firmware/assets retain their own terms.',
            'Kernel authors and KernelSU Next contributors retain their original attribution/licensing.',
        ],
        'licenses': [
            'Installer and included GPL-covered code: GPL-3.0-or-later; see ' + LICENSE_ENTRY + '.',
            'Firmware, proprietary assets, APKs, and other upstream components retain their own terms; this package grants no additional rights.',
        ],
        'images': records,
    }


def _notices(provenance):
    lines = [
        'X-NovaOS experimental TWRP ROM ZIP — source and license notices',
        '',
        'This package contains an experimental installer and partition images. It is not hardware-validated.',
        'The TWRP recovery is neither included nor modified. The ZIP is unsigned.',
        '',
        'Credits:',
    ]
    lines.extend('- ' + item for item in provenance['credits'])
    lines += [
        '',
        'Licensing:',
    ]
    lines.extend('- ' + item for item in provenance['licenses'])
    lines += [
        '',
        f'OneROM module/kernel credits and source provenance: see {CREDITS_ENTRY}.',
        'Pinned source provenance is recorded in installer/provenance.json and the repository manifests.',
        'Preserve original source credits, copyright notices, and license terms when redistributing components.',
    ]
    return '\n'.join(lines) + '\n'


def _safe_device_base(device_base):
    if not isinstance(device_base, str) or not re.fullmatch(r'/dev/block/[A-Za-z0-9_./-]+', device_base) or '..' in device_base:
        raise ValueError('Unsafe device base')
    return device_base


def _declared_profile(layout, model, codename):
    if layout == 'extreme-default':
        if (model, codename) != ('SM-G973F', 'beyond1lte'):
            raise ValueError('Fixed-size ExtremeROM Default is disabled for the SM-G975F candidate')
        profile_name = 'extreme-default.json'
    elif layout == 'extreme-structure':
        if (model, codename) != ('SM-G975F', 'beyond2lte'):
            raise ValueError('ExtremeROM structure-only profile is scoped to SM-G975F/beyond2lte')
        profile_name = 'extreme-structure-beyond2lte.json'
    else:
        if layout not in {'stock', 'content-sized', 'unknown'}:
            raise ValueError(f'Unsupported TWRP partition profile: {layout}')
        if (model, codename) == ('SM-G975F', 'beyond2lte'):
            raise ValueError('SM-G975F/beyond2lte TWRP ZIP requires the extreme-structure receipt')
        return None
    path = ROOT / 'integration/partition_layouts' / profile_name
    if path.is_symlink() or not path.is_file():
        raise ValueError('Pinned ExtremeROM partition profile is missing/unsafe')
    profile = json.loads(path.read_text())
    if (profile.get('schema_version') != 1 or profile.get('id') != layout
            or profile.get('model') != model or profile.get('codename') != codename):
        raise ValueError('Pinned ExtremeROM profile does not match the exact TWRP target')
    if layout == 'extreme-default':
        caps = profile.get('image_size_caps')
        if (profile.get('unit') != 'bytes' or not isinstance(caps, dict)
                or set(caps) != {'system', 'vendor', 'product', 'odm', 'prism', 'optics'}
                or any(type(size) is not int or size <= 0 for size in caps.values())):
            raise ValueError('Pinned ExtremeROM Default size profile is malformed')
    else:
        if ('image_size_caps' in profile
                or profile.get('image_partitions') != list(EXTREME_STRUCTURE_PARTITIONS)
                or profile.get('boot_components') != list(EXTREME_STRUCTURE_BOOT_COMPONENTS)
                or profile.get('repartitioner_partitions') != list(EXTREME_REPARTITIONER_PARTITIONS)
                or profile.get('reference_scope') != EXTREME_STRUCTURE_REFERENCE_SCOPE
                or profile.get('payload_format') != EXTREME_STRUCTURE_PAYLOAD_FORMAT
                or profile.get('payload_format_source') != EXTREME_STRUCTURE_PAYLOAD_FORMAT_SOURCE):
            raise ValueError('ExtremeROM structure profile must declare image roles without fixed size caps')
    return profile


def _declared_profile_caps(layout, model, codename):
    profile = _declared_profile(layout, model, codename)
    return profile.get('image_size_caps', {}) if profile else {}


def _declared_profile_structure(layout, model, codename):
    profile = _declared_profile(layout, model, codename)
    return profile.get('image_partitions', []) if profile else []


def _layout_guard(records, device_base, partition_profile_caps=None):
    profile_caps = partition_profile_caps or {}
    if (not isinstance(profile_caps, dict) or set(profile_caps) - FILESYSTEM_IMAGES
            or any(type(size) is not int or size <= 0 for size in profile_caps.values())):
        raise ValueError('Invalid read-only partition profile requirements')
    required = {record['name']: record['bytes'] for record in records}
    for name, capacity in profile_caps.items():
        required[name] = max(required.get(name, 0), capacity)
    guard = '#!/sbin/sh\n' + (ROOT / 'integration/recovery_layout_check.sh').read_text() + '\n'
    guard += ''.join(
        f'check_partition {name} {required[name]} || failures=1\n'
        for name in ORDER if name in required
    )
    guard += 'exit "$failures"\n'
    return guard


def _validate_image(name, source, temporary):
    if source.is_symlink() or not source.is_file():
        raise ValueError(f'Unsafe or missing image input: {name}.img')
    with source.open('rb') as stream:
        header = stream.read(32)
    if len(header) < 4:
        raise ValueError(f'Truncated image: {name}.img')
    sparse = struct.unpack('<I', header[:4])[0] == SPARSE_MAGIC
    if sparse and name in KERNEL_IMAGES:
        raise ValueError(f'Boot component must be a raw image, not sparse: {name}.img')
    raw = source
    if sparse:
        raw = Path(temporary) / f'{name}.raw.img'
        subprocess.run(['simg2img', str(source), str(raw)], check=True)
        if raw.is_symlink() or not raw.is_file():
            raise ValueError(f'simg2img produced an unsafe/missing image: {name}.img')
    if name in {'dtb', 'dtbo'}:
        with raw.open('rb') as stream:
            if stream.read(4) != DT_TABLE_MAGIC:
                label = 'DTB' if name == 'dtb' else 'DTBO'
                raise ValueError(f'Invalid Android {label} table image')
    elif name in {'boot', 'init_boot', 'vendor_boot'}:
        with raw.open('rb') as stream:
            if stream.read(8) != b'ANDROID!':
                raise ValueError(f'Invalid Android boot image: {name}.img')
    elif name in FILESYSTEM_IMAGES:
        verify_image(raw)
    else:
        raise ValueError(f'Unsupported image role: {name}')
    size = raw.stat().st_size
    if size <= 0 or size >= 2**53:
        raise ValueError('Invalid/unsupported image byte count')
    return raw, dict(name=name, bytes=size, sha256=sha256(raw))


def _read_manifest(archive):
    try:
        content = archive.read('installer/manifest.tsv').decode('ascii')
    except (KeyError, UnicodeDecodeError) as exc:
        raise ValueError('Missing/invalid installer image manifest') from exc
    records = []
    for line in content.splitlines():
        fields = line.split('\t')
        if len(fields) != 3:
            raise ValueError('Malformed installer manifest row')
        name, size_text, digest = fields
        if (name not in ORDER or not re.fullmatch(r'[1-9][0-9]*', size_text)
                or not re.fullmatch(r'[0-9a-f]{64}', digest)):
            raise ValueError('Invalid installer manifest row')
        records.append(dict(name=name, bytes=int(size_text), sha256=digest))
    names = [record['name'] for record in records]
    if (not REQUIRED <= set(names) or len(names) != len(set(names))
            or names != [name for name in ORDER if name in set(names)]
            or names[-1] != 'boot'):
        raise ValueError('Installer manifest has missing, duplicate, unsupported or unordered images')
    return records


def verify_package(package, *, expected_model='SM-G973F', expected_codename='beyond1lte',
                   images=None, raw_receipt=None):
    """Verify ZIP structure, payload hashes, target identity and TWRP entrypoint."""
    package = Path(package)
    if package.is_symlink() or not package.is_file() or package.stat().st_size <= 0:
        raise ValueError('Missing/unsafe TWRP ROM ZIP')
    if (expected_codename, expected_model) not in TWRP_ROM_TARGETS:
        raise ValueError('TWRP ZIP target must be exactly SM-G973F/beyond1lte or SM-G975F/beyond2lte')
    receipt_path = None
    receipt_data = None
    if raw_receipt is not None:
        receipt_path = Path(raw_receipt)
        if receipt_path.is_symlink() or not receipt_path.is_file():
            raise ValueError('Missing/unsafe raw image proof for TWRP package verification')
        receipt_data = json.loads(receipt_path.read_text())
    expected_source_manifests = {
        'artisan': _source_manifest('artisan-s10-files.json'),
        'onerom': _source_manifest('onerom.json'),
    }
    with zipfile.ZipFile(package) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise ValueError('TWRP ZIP contains duplicate paths')
        for info in infos:
            item = PurePosixPath(info.filename)
            mode = info.external_attr >> 16
            if (item.is_absolute() or '..' in item.parts or not item.parts
                    or stat.S_ISLNK(mode)):
                raise ValueError('TWRP ZIP contains an unsafe path or symlink')
        records = _read_manifest(archive)
        expected_entries = {
            UPDATE_BINARY,
            'installer/manifest.tsv',
            'installer/device-base',
            'installer/layout-check.sh',
            'installer/engine.sh',
            'installer/zip64-probe.txt',
            'installer/provenance.json',
            'REQUIRED-IMAGE-SIZES.json',
            'WARNING.txt',
            'NOTICES.txt',
            LICENSE_ENTRY,
            CREDITS_ENTRY,
        } | {f"images/{record['name']}.img" for record in records}
        if set(names) != expected_entries:
            raise ValueError('TWRP ZIP has unexpected/missing installer or payload entries')
        update_info = archive.getinfo(UPDATE_BINARY)
        if not ((update_info.external_attr >> 16) & 0o111):
            raise ValueError('TWRP update-binary is not executable')
        update_binary = archive.read(UPDATE_BINARY)
        if not update_binary.startswith(b'#!/sbin/sh\n') or b'ro.boot.em.model' not in update_binary:
            raise ValueError('TWRP update-binary entrypoint or target guard is missing')
        if b'block_image_update' in update_binary or b'new.dat.br' in update_binary:
            raise ValueError('Unexpected OTA/block-image installer path')
        device_base = archive.read('installer/device-base').decode('ascii')
        if device_base != _safe_device_base(device_base.strip()) + '\n':
            raise ValueError('Invalid installer device-base entry')
        partition_layout = receipt_data.get('partition_layout', 'unknown') if receipt_data else 'unknown'
        profile_caps = receipt_data.get('partition_profile_caps', {}) if receipt_data else {}
        partition_structure = receipt_data.get('partition_structure', []) if receipt_data else []
        expected_profile_caps = _declared_profile_caps(partition_layout, expected_model, expected_codename)
        expected_structure = _declared_profile_structure(partition_layout, expected_model, expected_codename)
        if profile_caps != expected_profile_caps or partition_structure != expected_structure:
            raise ValueError('RAW image proof does not match the selected partition structure/cap policy')
        expected_guard = _layout_guard(records, device_base.strip(), profile_caps).encode()
        if archive.read('installer/layout-check.sh') != expected_guard:
            raise ValueError('TWRP package capacity/mount guard differs from the reviewed host source')
        if archive.read('installer/engine.sh') != (ROOT / 'integration/new_installer/engine.sh').read_bytes():
            raise ValueError('TWRP package installer engine differs from reviewed host source')
        if update_binary != _update_binary(expected_model):
            raise ValueError('TWRP package update-binary differs from the exact target-locked host template')
        if archive.read('installer/zip64-probe.txt') != b'XNOVA_RAW_V1\n':
            raise ValueError('TWRP ZIP64 probe entry is invalid')
        warning = archive.read('WARNING.txt').decode('utf-8')
        if ('NOT HARDWARE-VALIDATED' not in warning or 'unsigned' not in warning.lower()
                or 'does not verify the physical partition table' not in warning.lower()
                or 'read-only installer guard' not in warning.lower()):
            raise ValueError('TWRP package warning must disclose hardware, layout and signature status')
        try:
            sizes = json.loads(archive.read('REQUIRED-IMAGE-SIZES.json'))
            provenance = json.loads(archive.read('installer/provenance.json'))
        except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError('TWRP package metadata is missing or malformed') from exc
        expected_sizes = {record['name']: record['bytes'] for record in records}
        if (sizes.get('model') != expected_model or sizes.get('codename') != expected_codename
                or sizes.get('image_size_bytes') != expected_sizes
                or sizes.get('physical_layout_verified') is not False
                or sizes.get('partition_layout') != partition_layout
                or sizes.get('partition_profile_caps') != profile_caps
                or sizes.get('partition_structure', []) != partition_structure
                or provenance.get('model') != expected_model
                or provenance.get('codename') != expected_codename
                or provenance.get('recovery_included') is not False
                or provenance.get('recovery_modified') is not False
                or provenance.get('hardware_validated') is not False
                or provenance.get('images') != records
                or not isinstance(provenance.get('source_manifests'), dict)
                or not isinstance(provenance.get('credits'), list)
                or not isinstance(provenance.get('licenses'), list)
                or not any('GPL-3.0-or-later' in item for item in provenance.get('licenses', []))
                or provenance.get('source_manifests') != expected_source_manifests
                or (receipt_data is not None
                    and (provenance.get('raw_image_proof_sha256') != sha256(receipt_path)
                         or provenance.get('firmware_lock_sha256') != receipt_data.get('firmware_lock_sha256')
                         or provenance.get('build_identity') != receipt_data.get('build')))):
            raise ValueError('TWRP package metadata does not match the target/output contract')
        if LICENSE_FILE.is_symlink() or not LICENSE_FILE.is_file():
            raise ValueError('Retained GPL license text is missing/unsafe')
        if archive.read(LICENSE_ENTRY) != LICENSE_FILE.read_bytes():
            raise ValueError('TWRP ZIP GPL license text differs from the retained source license')
        credits_file = _credits_file()
        if archive.read(CREDITS_ENTRY) != credits_file.read_bytes():
            raise ValueError('TWRP ZIP OneROM credits differ from the retained source')
        notices = archive.read('NOTICES.txt').decode('utf-8')
        if any(name not in notices for name in ('ArtisanROM', 'OneROM', 'ExtremeROM', 'UN1CA', 'Samsung')):
            raise ValueError('TWRP ZIP attribution notices are incomplete')
        package_records = []
        for record in records:
            member = f"images/{record['name']}.img"
            with archive.open(member) as stream:
                size, digest = _sha256_stream(stream)
            if size != record['bytes'] or digest != record['sha256']:
                raise ValueError(f'TWRP ZIP payload size/hash mismatch: {member}')
            if images is not None:
                source = Path(images) / f"{record['name']}.img"
                if source.is_symlink() or not source.is_file() or source.stat().st_size != size or sha256(source) != digest:
                    raise ValueError(f'TWRP ZIP payload differs from the verified image bundle: {member}')
            package_records.append(dict(record))
        # Reading every member above also exercises ZIP decompression and CRCs.
    if raw_receipt is not None:
        if images is None:
            raise ValueError('Image bundle path is required with a raw-image receipt')
        verify_raw_bundle(images, expected_model, expected_codename,
                          receipt=raw_receipt, verify_hashes=True)
    return {
        'status': 'twrp-rom-zip-host-verified',
        'package': package.name,
        'bytes': package.stat().st_size,
        'sha256': sha256(package),
        'target_model': expected_model,
        'target_codename': expected_codename,
        'images': [record['name'] for record in package_records],
        'image_count': len(package_records),
        'twrp_update_binary': UPDATE_BINARY,
        'recovery_included': False,
        'recovery_modified': False,
        'hardware_validated': False,
    }


def build(images, output, device_base=DEVICE_BASE_DEFAULT, *, receipt=None,
          expected_model='SM-G973F', expected_codename='beyond1lte'):
    images = Path(images)
    output = Path(output)
    if (expected_codename, expected_model) not in TWRP_ROM_TARGETS:
        raise ValueError('TWRP ZIP target must be exactly SM-G973F/beyond1lte or SM-G975F/beyond2lte')
    device_base = _safe_device_base(device_base)
    if images.is_symlink() or not images.is_dir():
        raise ValueError('Missing/unsafe RAW image directory')
    input_entries = list(images.iterdir())
    if any(path.is_symlink() or not path.is_file() or path.suffix != '.img' for path in input_entries):
        raise ValueError('RAW image directory may contain only regular .img files')
    available = {path.stem for path in input_entries}
    if len(available) != len(input_entries) or not REQUIRED <= available or available - set(ORDER):
        raise ValueError('Missing required or unsupported image role (no recovery/data/EFS writes)')
    receipt_data = None
    if receipt is not None:
        verify_raw_bundle(images, expected_model, expected_codename,
                          receipt=receipt, verify_hashes=True)
        if isinstance(receipt, (str, Path)):
            receipt_path = Path(receipt)
            if receipt_path.is_symlink() or not receipt_path.is_file():
                raise ValueError('Missing/unsafe raw image proof for TWRP package build')
            receipt_data = json.loads(receipt_path.read_text())
        else:
            raise ValueError('TWRP ROM ZIP construction requires a persisted raw image proof receipt')
    partition_layout = receipt_data.get('partition_layout', 'unknown') if receipt_data else 'unknown'
    profile_caps = receipt_data.get('partition_profile_caps', {}) if receipt_data else {}
    partition_structure = receipt_data.get('partition_structure', []) if receipt_data else []
    if (profile_caps != _declared_profile_caps(partition_layout, expected_model, expected_codename)
            or partition_structure != _declared_profile_structure(partition_layout, expected_model, expected_codename)):
        raise ValueError('RAW image proof does not match the selected partition structure/cap policy')
    if output.exists() or output.is_symlink():
        raise ValueError('Refusing to replace an existing package')
    if output.parent.is_symlink() or not output.parent.is_dir():
        raise ValueError('TWRP package output directory is missing/unsafe')
    records = []
    created = False
    try:
        with tempfile.TemporaryDirectory(prefix='xnova-twrp-host-', dir=output.parent) as temporary:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
                created = True
                for name in ORDER:
                    if name not in available:
                        continue
                    source = images / (name + '.img')
                    raw, record = _validate_image(name, source, temporary)
                    records.append(record)
                    archive.write(raw, f'images/{name}.img')
                    if raw != source:
                        raw.unlink()
                manifest = ''.join(
                    f"{record['name']}\t{record['bytes']}\t{record['sha256']}\n"
                    for record in records
                )
                archive.writestr('installer/manifest.tsv', manifest)
                archive.writestr('installer/device-base', device_base + '\n')
                archive.writestr('installer/layout-check.sh', _layout_guard(records, device_base, profile_caps))
                archive.write(ROOT / 'integration/new_installer/engine.sh', 'installer/engine.sh')
                info = zipfile.ZipInfo(UPDATE_BINARY)
                info.external_attr = (stat.S_IFREG | 0o755) << 16
                archive.writestr(info, _update_binary(expected_model))
                archive.writestr('REQUIRED-IMAGE-SIZES.json', json.dumps({
                    'model': expected_model,
                    'codename': expected_codename,
                    'partition_layout': partition_layout,
                    'partition_profile_caps': profile_caps,
                    'partition_structure': partition_structure,
                    'physical_layout_verified': False,
                    'installer': 'xnova-twrp-raw-v1-experimental',
                    'image_size_bytes': {record['name']: record['bytes'] for record in records},
                }, indent=2) + '\n')
                if partition_layout == 'extreme-structure':
                    profile_warning = 'Selected ExtremeROM partition-name reference profile applies no fixed image-size cap at build time. '
                elif profile_caps:
                    profile_warning = 'Selected fixed profile image-size caps were enforced during image construction. '
                else:
                    profile_warning = 'No fixed profile image-size cap is enforced by this ZIP. '
                archive.writestr(
                    'WARNING.txt',
                    f'EXPERIMENTAL TWRP ROM ZIP for {expected_model} / {expected_codename}: '
                    'NOT HARDWARE-VALIDATED; unsigned; not release-approved.\n'
                    'The package contains RAW partition images and an update-binary script; it does not '
                    'include or modify TWRP/recovery. TWRP must permit unsigned test packages.\n'
                    'REQUIRED-IMAGE-SIZES.json lists exact image byte sizes. ' + profile_warning +
                    'A read-only installer guard checks declared target paths, actual image capacities and '
                    'mount state before any write, and aborts on failure. This does not verify the physical '
                    'partition table or prove any repartition is installed.\n'
                    'No partition resizing, repartitioning or filesystem formatting is performed. Confirm '
                    'the actual device layout independently; an image may exceed a stock partition.\n'
                    'Writes are non-atomic; interruption after the first partition write may leave the '
                    'device unbootable. Requires userdata mounted and free staging space for all images.\n'
                    'No automatic mount, OTA new.dat.br, transfer.list, block_image_update, modem, EFS '
                    'or recovery image is included. Keep backups and a stock restore procedure.\n',
                )
                provenance = _provenance(
                    records, receipt, model=expected_model, codename=expected_codename,
                )
                if LICENSE_FILE.is_symlink() or not LICENSE_FILE.is_file():
                    raise ValueError('Retained GPL license text is missing/unsafe')
                archive.write(LICENSE_FILE, LICENSE_ENTRY)
                credits_file = _credits_file()
                archive.write(credits_file, CREDITS_ENTRY)
                archive.writestr('NOTICES.txt', _notices(provenance))
                archive.writestr('installer/provenance.json', json.dumps(provenance, indent=2) + '\n')
                # Last entry deliberately exercises ZIP64 local-header handling.
                with archive.open('installer/zip64-probe.txt', 'w', force_zip64=True) as probe:
                    probe.write(b'XNOVA_RAW_V1\n')
        verify_package(
            output, expected_model=expected_model, expected_codename=expected_codename,
            images=images, raw_receipt=receipt,
        )
        return records
    except BaseException:
        if created:
            output.unlink(missing_ok=True)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path,
                        help='Host-verified raw-image proof receipt for this exact target')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--device-base', default=DEVICE_BASE_DEFAULT)
    parser.add_argument('--model', choices=sorted({model for _codename, model in TWRP_ROM_TARGETS}),
                        default='SM-G973F')
    parser.add_argument('--codename', choices=sorted({codename for codename, _model in TWRP_ROM_TARGETS}),
                        default='beyond1lte')
    parser.add_argument('--experimental', action='store_true',
                        help='Acknowledge candidate, not hardware validated or release-approved')
    args = parser.parse_args(argv)
    if not args.experimental:
        parser.error('--experimental is required; no package is release-approved')
    try:
        records = build(
            args.images, args.output, args.device_base, receipt=args.receipt,
            expected_model=args.model, expected_codename=args.codename,
        )
        print(json.dumps({
            'package': str(args.output),
            'sha256': sha256(args.output),
            'images': [record['name'] for record in records],
            'status': 'experimental-twrp-zip-not-hardware-validated',
        }, indent=2), flush=True)
        return 0
    except (OSError, ValueError, subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        print(f'TWRP ROM ZIP build stopped: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
