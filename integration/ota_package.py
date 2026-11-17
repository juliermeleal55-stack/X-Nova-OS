#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Structural validator for the legacy static-partition Artisan S10 OTA ZIP."""
import re
import zipfile

FILESYSTEM_PARTITIONS = {
    'system', 'vendor', 'product', 'odm', 'system_ext', 'prism', 'optics',
    'vendor_dlkm', 'odm_dlkm', 'system_dlkm',
}


def _ota_update_operations(script):
    """Parse and validate the static-partition block writes used by S10 OTAs."""
    calls = list(re.finditer(r'\bblock_image_update\s*\(', script))
    pattern = re.compile(
        r'\bblock_image_update\s*\(\s*"(?P<device>[^"\r\n]+)"\s*,\s*'
        r'package_extract_file\s*\(\s*"(?P<transfer>[^"\r\n]+)"\s*\)\s*,\s*'
        r'"(?P<payload>[^"\r\n]+)"\s*,\s*"(?P<patch>[^"\r\n]+)"\s*\)'
    )
    matches = list(pattern.finditer(script))
    if not calls or len(matches) != len(calls):
        raise ValueError('Installer has missing or malformed block_image_update operations')
    operations = {}
    target_pattern = re.compile(r'/dev/block/(?:[A-Za-z0-9_.-]+/)*by-name/([a-z_]+)')
    for match in matches:
        target_match = target_pattern.fullmatch(match['device'])
        if not target_match:
            raise ValueError('OTA block writes must use an explicit static by-name partition')
        partition = target_match.group(1)
        expected = (f'{partition}.transfer.list', f'{partition}.new.dat.br', f'{partition}.patch.dat')
        actual = (match['transfer'], match['payload'], match['patch'])
        if actual != expected:
            raise ValueError(f'OTA payload/transfer-list names do not match target partition {partition}')
        if partition in operations:
            raise ValueError(f'Duplicate block_image_update operation for {partition}')
        operations[partition] = actual
    return operations


def check_package(path, model='SM-G975F', allowed_partitions=None):
    """Reject malformed, wrong-device, RAW, recovery, or unsafe Artisan OTA ZIPs."""
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len({item.filename for item in entries}) != len(entries):
            raise ValueError('Duplicate ZIP entries; do not patch packages with ambiguous installer paths')
        if any(item.flag_bits & 1 or item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
               for item in entries):
            raise ValueError('Unsupported encrypted/compression ZIP format for recovery')
        if archive.testzip() is not None:
            raise ValueError('Corrupted ZIP')
        names = set(archive.namelist())
        required = {
            'META-INF/com/google/android/update-binary',
            'META-INF/com/google/android/updater-script',
            'boot.img', 'dtb.img', 'dtbo.img',
            'system.new.dat.br', 'system.transfer.list',
        }
        if not required <= names:
            raise ValueError(f'Missing installer components: {required - names}')
        if any(archive.getinfo(name).file_size == 0 for name in required):
            raise ValueError('Empty installer component')

        script = archive.read('META-INF/com/google/android/updater-script').decode()
        models = set(re.findall(r'SM-[A-Z0-9]+', script))
        if models != {model}:
            raise ValueError('Unexpected device assertions')
        if re.search(r'/by-name/(?:recovery|vendor_recovery|recovery_[ab])(?:["/]|$)', script, re.I):
            raise ValueError('Recovery partition writes are not allowed in this ROM package')
        if re.search(r'\brun_program\s*\(\s*"[^"\r\n]*(?:e2fsck|resize2fs|sgdisk|parted|mkfs)[^"\r\n]*"', script, re.I):
            raise ValueError('Unreviewed filesystem resize/format or repartition postinstall is forbidden')

        raw_filesystem_images = {f'{partition}.img' for partition in FILESYSTEM_PARTITIONS} & names
        if raw_filesystem_images:
            raise ValueError('Legacy Artisan OTA ZIP must not contain RAW filesystem .img payloads')
        allowed_kernel_images = {'boot.img', 'dtb.img', 'dtbo.img'}
        image_entries = {name for name in names if name.endswith('.img')}
        if image_entries - allowed_kernel_images:
            raise ValueError(f'Unsupported RAW/recovery image payloads: {sorted(image_entries - allowed_kernel_images)}')
        forbidden_images = {'recovery.img', 'recovery.bin', 'twrp.img', 'super.img',
                            'init_boot.img', 'vendor_boot.img'} & names
        if forbidden_images:
            raise ValueError(f'Unsupported recovery/super/boot payloads: {sorted(forbidden_images)}')

        payloads = {
            match.group(1) for name in names
            if (match := re.fullmatch(r'([a-z_]+)\.new\.dat\.br', name))
        }
        if 'system' not in payloads:
            raise ValueError('Missing Brotli-compressed system.new.dat.br payload')
        invalid_payloads = {
            name for name in names
            if re.fullmatch(r'[a-z_]+\.new\.dat(?:\.[A-Za-z0-9]+)?', name)
            and not re.fullmatch(r'[a-z_]+\.new\.dat\.br', name)
        }
        if invalid_payloads:
            raise ValueError(f'Unsupported non-Brotli OTA payloads: {sorted(invalid_payloads)}')
        transfer_lists = {
            match.group(1) for name in names
            if (match := re.fullmatch(r'([a-z_]+)\.transfer\.list', name))
        }
        if transfer_lists != payloads:
            raise ValueError('OTA payloads and transfer lists do not correspond one-to-one')

        operations = _ota_update_operations(script)
        if payloads != set(operations):
            raise ValueError('OTA payloads and block_image_update operations do not correspond one-to-one')
        partition_allowlist = set(allowed_partitions) if allowed_partitions is not None else FILESYSTEM_PARTITIONS
        if (payloads | set(operations)) - partition_allowlist:
            raise ValueError('Installer references unsupported target partitions')
