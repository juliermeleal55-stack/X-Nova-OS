#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build/verify the experimental TWRP ROM ZIP from host-verified RAW images."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from integration.package_inputs import atomic_json
from integration.raw_images import PROOF_ROOT as RAW_PROOF_ROOT
from integration.raw_images import build as build_raw_images
from integration.raw_images import verify_bundle as verify_raw_bundle
from integration.targets import from_marker
from integration.twrp_zip_builder import build as build_twrp_zip
from integration.twrp_zip_builder import sha256, verify_package as verify_twrp_zip

OUTPUT_ROOT = Path('out/twrp-zips')
PROOF_ROOT = Path('out/twrp-zip-proof')


def _safe_file(path, description):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'Missing/unsafe {description}')
    return path


def _positive_label(name, default):
    value = os.environ.get(name)
    if value in (None, ''):
        return default
    if not re.fullmatch(r'[1-9][0-9]*', value):
        raise ValueError(f'{name} must be a positive decimal value')
    return value


def _package_name(model):
    version = os.environ.get('BEYOUD_ALPHA_VERSION', '3.2')
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*', version):
        raise ValueError('BEYOUD_ALPHA_VERSION must be numeric dot-separated components')
    run_number = _positive_label('GITHUB_RUN_NUMBER', 'local')
    run_attempt = _positive_label('GITHUB_RUN_ATTEMPT', '1')
    return (
        f'X-NovaOS-Alpha-{version}-{model}-Build-{run_number}-Attempt-{run_attempt}'
        '-TWRP-UNTESTED.zip'
    )


def _workspace_identity(workspace):
    marker_path = _safe_file(workspace / 'BEYOUD-WORKSPACE.json', 'workspace provenance marker')
    marker = json.loads(marker_path.read_text())
    codename, device = from_marker(marker)
    if (codename, device['model']) != ('beyond1lte', 'SM-G973F'):
        raise ValueError('The reviewed TWRP ROM ZIP currently supports SM-G973F / beyond1lte only')
    return marker, codename, device['model']


def _output_paths(workspace, codename):
    zip_dir = workspace / OUTPUT_ROOT / codename
    proof_dir = workspace / PROOF_ROOT
    zip_path = zip_dir / _package_name('SM-G973F')
    proof_path = proof_dir / f'{codename}.json'
    raw_dir = workspace / 'out/raw-images' / codename
    raw_receipt = workspace / RAW_PROOF_ROOT / f'{codename}.json'
    return zip_dir, zip_path, proof_dir, proof_path, raw_dir, raw_receipt


def verify_workspace(workspace):
    """Validate the delivered ZIP, its exact image inputs, and private receipts."""
    workspace = Path(workspace).resolve()
    marker, codename, model = _workspace_identity(workspace)
    lock_path = _safe_file(workspace / 'out/firmware-lock.json', 'verified firmware lock')
    zip_dir, expected_zip, proof_dir, proof_path, raw_dir, raw_receipt = _output_paths(workspace, codename)
    for path in (workspace / OUTPUT_ROOT, zip_dir, proof_dir,
                 workspace / 'out/raw-images', raw_dir,
                 workspace / RAW_PROOF_ROOT, raw_receipt.parent):
        if path.is_symlink():
            raise ValueError(f'Unsafe TWRP package path component: {path}')
    if not zip_dir.is_dir():
        raise ValueError('Missing/unsafe TWRP ZIP output directory')
    packages = sorted(zip_dir.glob('*.zip'))
    if len(packages) != 1 or packages[0].is_symlink() or packages[0] != expected_zip:
        raise ValueError('Expected exactly one named TWRP ROM ZIP in the target output directory')
    if proof_dir.is_symlink() or not proof_dir.is_dir():
        raise ValueError('Missing/unsafe TWRP ZIP proof directory')
    proof_path = _safe_file(proof_path, 'private TWRP ZIP proof receipt')
    raw_receipt = _safe_file(raw_receipt, 'private RAW image proof receipt')
    if raw_dir.is_symlink() or not raw_dir.is_dir():
        raise ValueError('Missing/unsafe verified RAW image staging directory')

    raw_report = verify_raw_bundle(
        raw_dir, expected_model=model, expected_codename=codename,
        receipt=raw_receipt, verify_hashes=True,
    )
    if json.loads(raw_receipt.read_text()).get('firmware_lock_sha256') != sha256(lock_path):
        raise ValueError('RAW image proof does not match the verified firmware lock')
    package = packages[0]
    zip_report = verify_twrp_zip(
        package, expected_model=model, expected_codename=codename,
        images=raw_dir, raw_receipt=raw_receipt,
    )
    receipt = json.loads(proof_path.read_text())
    expected_receipt = {
        'schema_version': 1,
        'format': 'twrp-rom-zip-v1',
        'status': 'host-verified-not-hardware-validated',
        'target_model': model,
        'target_codename': codename,
        'package_filename': package.name,
        'package_bytes': package.stat().st_size,
        'package_sha256': sha256(package),
        'raw_image_proof_sha256': sha256(raw_receipt),
        'firmware_lock_sha256': sha256(lock_path),
        'recovery_protocol': 'TWRP Android update-binary interface',
        'recovery_included': False,
        'recovery_modified': False,
        'hardware_validated': False,
        'release_published': False,
        'images': raw_report['images'],
    }
    for key, value in expected_receipt.items():
        if receipt.get(key) != value:
            raise ValueError(f'TWRP ZIP proof mismatch: {key}')
    return {
        'status': zip_report['status'],
        'target_model': model,
        'target_codename': codename,
        'package': str(package),
        'package_bytes': zip_report['bytes'],
        'package_sha256': zip_report['sha256'],
        'images': zip_report['images'],
        'image_count': zip_report['image_count'],
        'recovery_included': False,
        'recovery_modified': False,
        'hardware_validated': False,
        'firmware_lock_sha256': sha256(lock_path),
        'source_commit': marker.get('source_commit'),
    }


def build_workspace(workspace):
    """Generate intermediate RAW images, then one TWRP-installable ZIP."""
    workspace = Path(workspace).resolve()
    if os.environ.get('BEYOUD_OUTPUT_FORMAT', 'twrp-zip') != 'twrp-zip':
        raise ValueError('Only the TWRP-installable ROM ZIP output format is supported')
    marker, codename, model = _workspace_identity(workspace)
    out = workspace / 'out'
    if out.is_symlink() or not out.is_dir():
        raise ValueError('Missing/unsafe build output directory')
    zip_dir, zip_path, proof_dir, proof_path, raw_dir, raw_receipt = _output_paths(workspace, codename)
    lock_path = _safe_file(out / 'firmware-lock.json', 'verified firmware lock')
    for path, description in ((out / 'twrp-zips', 'TWRP ZIP root'),
                              (zip_dir, 'TWRP ZIP output directory'),
                              (proof_dir, 'private TWRP ZIP proof directory'),
                              (out / 'raw-images', 'RAW image staging root'),
                              (out / RAW_PROOF_ROOT.relative_to('out'), 'RAW image proof root')):
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError(f'Unsafe {description}')
    if proof_path.is_symlink() or proof_path.exists():
        raise ValueError('Refusing to replace an existing TWRP ZIP proof receipt')
    proof_partial = proof_path.with_suffix('.partial')
    if proof_partial.is_symlink() or proof_partial.exists():
        raise ValueError('Refusing to overwrite an existing/unsafe TWRP ZIP proof temporary')

    if raw_dir.exists() or raw_dir.is_symlink() or raw_receipt.exists() or raw_receipt.is_symlink():
        if raw_dir.is_symlink() or raw_receipt.is_symlink() or not raw_dir.is_dir() or not raw_receipt.is_file():
            raise ValueError('RAW image output is partial/unsafe; use a fresh workspace')
        verify_raw_bundle(raw_dir, model, codename, receipt=raw_receipt, verify_hashes=True)
    else:
        build_raw_images(workspace)
        raw_receipt = _safe_file(raw_receipt, 'private RAW image proof receipt')

    if json.loads(raw_receipt.read_text()).get('firmware_lock_sha256') != sha256(lock_path):
        raise ValueError('RAW image proof does not match the verified firmware lock')
    if zip_dir.exists():
        if list(zip_dir.iterdir()):
            raise ValueError('TWRP ZIP output directory is not empty; preserve prior artifacts and use a fresh workspace')
    else:
        zip_dir.mkdir(parents=True)
    proof_dir.mkdir(parents=True, exist_ok=True)
    if zip_path.exists() or zip_path.is_symlink():
        raise ValueError('Refusing to replace an existing TWRP ROM ZIP')

    created_package = False
    try:
        records = build_twrp_zip(raw_dir, zip_path, receipt=raw_receipt)
        created_package = True
        report = verify_twrp_zip(
            zip_path, expected_model=model, expected_codename=codename,
            images=raw_dir, raw_receipt=raw_receipt,
        )
        proof = {
            'schema_version': 1,
            'format': 'twrp-rom-zip-v1',
            'status': 'host-verified-not-hardware-validated',
            'target_model': model,
            'target_codename': codename,
            'package_filename': zip_path.name,
            'package_bytes': zip_path.stat().st_size,
            'package_sha256': sha256(zip_path),
            'raw_image_proof_sha256': sha256(raw_receipt),
            'firmware_lock_sha256': sha256(lock_path),
            'recovery_protocol': 'TWRP Android update-binary interface',
            'recovery_included': False,
            'recovery_modified': False,
            'hardware_validated': False,
            'release_published': False,
            'images': report['images'],
            'image_records': records,
            'installer_entrypoint': 'META-INF/com/google/android/update-binary',
            'signature_status': 'unsigned-test-package',
        }
        atomic_json(proof_path, proof)
        result = verify_workspace(workspace)
        result['proof'] = str(proof_path)
        return result
    except BaseException:
        if created_package:
            zip_path.unlink(missing_ok=True)
        proof_path.unlink(missing_ok=True)
        raise


def main():
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} /absolute/workspace', file=sys.stderr)
        return 64
    try:
        report = build_workspace(Path(sys.argv[1]))
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f'TWRP ROM ZIP build stopped: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
