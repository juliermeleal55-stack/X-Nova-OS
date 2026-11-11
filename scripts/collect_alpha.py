#!/usr/bin/env python3
"""Structural alpha artifact checks; never a certification of boot or safety."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integration.targets import from_marker
from integration.package_inputs import load as load_package_inputs, image_caps


def check_package(path, model="SM-G975F", allowed_partitions=None):
    with zipfile.ZipFile(path) as archive:
        entries=archive.infolist()
        if len({item.filename for item in entries})!=len(entries):
            raise ValueError('Duplicate ZIP entries; do not patch packages with ambiguous installer paths')
        if any(item.flag_bits & 1 or item.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED) for item in entries):
            raise ValueError('Unsupported encrypted/compression ZIP format for recovery')
        if archive.testzip() is not None:
            raise ValueError('Corrupted ZIP')
        names = set(archive.namelist())
        required = {'META-INF/com/google/android/update-binary',
                    'META-INF/com/google/android/updater-script', 'boot.img', 'dtbo.img'}
        if not required <= names:
            raise ValueError(f'Missing installer components: {required - names}')
        if any(archive.getinfo(name).file_size==0 for name in required):
            raise ValueError('Empty installer component')
        script = archive.read('META-INF/com/google/android/updater-script').decode()
        models = set(re.findall(r'SM-[A-Z0-9]+', script))
        if models != {model}:
            raise ValueError('Unexpected device assertions')
        if not any(name.startswith('system.') and '.dat' in name for name in names):
            raise ValueError('Missing system payload')
        if allowed_partitions is not None:
            payloads = {match.group(1) for name in names if (match := re.fullmatch(r'([a-z_]+)\.new\.dat(?:\.br)?', name))}
            writes = set(re.findall(r'block_image_update\(\s*"[^"\n]*/([^/"\n]+)"', script))
            if (payloads | writes) - set(allowed_partitions):
                raise ValueError('Installer references unsupported target partitions')
            if {'super.img','init_boot.img','vendor_boot.img'} & names:
                raise ValueError('Unsupported static S10 boot/super payload')
        for image in ('boot.img', 'dtbo.img'):

            if archive.getinfo(image).file_size == 0:
                raise ValueError(f'Empty {image}')


def collect(workspace, destination, alpha_version=None, build_number=None, run_attempt=1):
    """Validate and label an alpha artifact without rewriting its ZIP bytes.

    The optional public identity keeps older/manual local invocations backwards
    compatible. CI supplies all three values so every requested X-NovaOS build
    carries its Alpha version, GitHub run number, and retry attempt.
    """
    if alpha_version is not None:
        if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*', alpha_version):
            raise ValueError('Alpha version must contain only numeric dot-separated components')
        if type(build_number) is not int or build_number < 1:
            raise ValueError('A positive GitHub build number is required with the public Alpha version')
        if type(run_attempt) is not int or run_attempt < 1:
            raise ValueError('Run attempt must be a positive integer')
    elif build_number is not None or run_attempt != 1:
        raise ValueError('Build number/attempt require an explicit public Alpha version')

    marker = json.loads((workspace / 'BEYOUD-WORKSPACE.json').read_text())
    codename, device = from_marker(marker)
    model = device['model']
    candidates = list((workspace / 'out').glob(f'*alpha1*{codename}*.zip'))
    if len(candidates) != 1:
        raise ValueError(f'Expected exactly one alpha ZIP, found {len(candidates)}')
    source = candidates[0]
    inputs = load_package_inputs(workspace)
    check_package(source, model, image_caps(inputs))
    layout = inputs.get('partition_layout', {}).get('id', 'stock')
    try:
        suffix = {
            'stock': '',
            'extreme-default': '-EXTREME-DEFAULT-REPARTITION',
            'content-sized': '-CUSTOM-REPARTITION-REQUIRED',
        }[layout]
    except KeyError as exc:
        raise ValueError(f'Unsupported package partition layout: {layout}') from exc

    if alpha_version is None:
        filename = f'Beyoud-{model}-0.1.0-alpha1{suffix}-UNTESTED.zip'
        display_identity = None
    else:
        display_identity = f'X-NovaOS Alpha {alpha_version} — build #{build_number}, attempt {run_attempt}'
        filename = (
            f'X-NovaOS-{model}-Alpha-{alpha_version}-Build-{build_number}'
            f'-Attempt-{run_attempt}{suffix}-UNTESTED.zip'
        )

    destination.mkdir(parents=True, exist_ok=False)
    output = destination / filename
    try:
        os.link(source, output)  # Avoid doubling a multi-GB package on the same filesystem.
    except OSError:
        shutil.copyfile(source, output)
    digest = hashlib.sha256()
    with output.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    sha256 = digest.hexdigest()
    (destination / 'SHA256SUMS').write_text(f'{sha256}  {filename}\n')
    warning = (
        f'{display_identity}\n' if display_identity else ''
    ) + (
        f'EXPERIMENTAL UNTESTED ALPHA — {model} ONLY\n'
        'Build success and structural checks DO NOT prove boot or flash safety.\n'
        'May erase data, fail to boot or break calls, camera, encryption and other features.\n'
        'Not for a primary phone. No hardware validation has been performed.\n'
        'Have an independently verified stock recovery procedure and backups before any test.\n'
    )
    (destination / 'WARNING.txt').write_text(warning)
    if layout == 'content-sized':
        with zipfile.ZipFile(source) as archive:
            requirements = archive.read('REQUIRED-IMAGE-SIZES.json')
        (destination / 'REQUIRED-IMAGE-SIZES.json').write_bytes(requirements)
        with (destination / 'WARNING.txt').open('a') as stream:
            stream.write('CUSTOM REPARTITION REQUIRED: size physical partitions to REQUIRED-IMAGE-SIZES.json before flashing. No fixed stock/ExtremeROM sizes were enforced at build time. The ZIP does NOT repartition automatically.\n')
    elif layout != 'stock':
        (destination / 'REQUIRED-PARTITION-LAYOUT.json').write_text(json.dumps(inputs['partition_layout'], indent=2) + '\n')
        with (destination / 'WARNING.txt').open('a') as stream:
            stream.write('REQUIRES DEFAULT EXTREMEROM REPARTITION: system 7000 MiB, vendor/product 1500 MiB; ODM 4 MiB, prism 600 MiB, optics 30 MiB. NOT FOR STOCK LAYOUT.\n')
    lock = workspace / 'out/firmware-lock.json'
    if lock.is_file():
        shutil.copyfile(lock, destination / 'firmware-lock.json')
    (destination / 'provenance.json').write_text(json.dumps(marker, indent=2) + '\n')
    if alpha_version is not None:
        run_id = os.environ.get('GITHUB_RUN_ID')
        repository = os.environ.get('GITHUB_REPOSITORY')
        server = os.environ.get('GITHUB_SERVER_URL', 'https://github.com').rstrip('/')
        run_url = f'{server}/{repository}/actions/runs/{run_id}' if repository and run_id else None
        build_info = {
            'project': 'X-NovaOS',
            'version': f'Alpha {alpha_version}',
            'build_number': build_number,
            'run_attempt': run_attempt,
            'target_codename': codename,
            'target_model': model,
            'partition_layout': layout,
            'status': 'EXPERIMENTAL / UNTESTED',
            'release_published': False,
            'hardware_validated': False,
            'artifact_filename': filename,
            'sha256': sha256,
            'github_run_id': run_id,
            'github_run_url': run_url,
            'source_commit': os.environ.get('GITHUB_SHA'),
            'zip_bytes_modified': False,
        }
        (destination / 'BUILD-INFO.json').write_text(json.dumps(build_info, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--alpha-version', help='Public numeric Alpha version, for example 3.1')
    parser.add_argument('--build-number', type=int, help='GitHub Actions run number')
    parser.add_argument('--run-attempt', type=int, default=1, help='GitHub Actions retry number')
    args = parser.parse_args()
    collect(args.workspace, args.destination, args.alpha_version, args.build_number, args.run_attempt)
