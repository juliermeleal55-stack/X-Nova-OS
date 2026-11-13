#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the verified intermediate RAW partition images used by the TWRP ZIP.

This helper constructs and verifies image payloads only; it never flashes a
device. The TWRP ZIP wrapper packages these intermediates separately and does
not run the legacy OTA builder, img2sdat, Brotli, or signapk.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from integration.installer_integrity import EROFS_MAGIC, SPARSE_MAGIC, verify_image
from integration.package_inputs import atomic_json, image_caps, load as load_package_inputs
from integration.targets import from_marker

# Static filesystem images emitted by the pinned S10 work-tree assembler. Extra
# partitions are included when the completed target tree contains them.
FILESYSTEM_ORDER = (
    'system', 'vendor', 'product', 'odm', 'prism', 'optics', 'system_ext',
    'vendor_dlkm', 'odm_dlkm', 'system_dlkm',
)
# The pinned S10 kernel builder explicitly produces all three of boot, dtb and
# dtbo; init_boot/vendor_boot remain optional for targets that provide them.
KERNEL_ORDER = ('dtb', 'dtbo', 'init_boot', 'vendor_boot', 'boot')
IMAGE_ORDER = FILESYSTEM_ORDER + KERNEL_ORDER
REQUIRED_FILESYSTEM = {'system', 'vendor', 'product'}
REQUIRED_KERNEL = {'boot', 'dtb', 'dtbo'}
REQUIRED_IMAGES = REQUIRED_FILESYSTEM | REQUIRED_KERNEL
PROOF_ROOT = Path('out/raw-image-proof')


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _positive_env(name):
    value = os.environ.get(name)
    if value in (None, ''):
        return None
    try:
        number = int(value)
    except ValueError as exc:
        raise ValueError(f'{name} must be a positive integer') from exc
    if number < 1:
        raise ValueError(f'{name} must be a positive integer')
    return number


def _build_identity(model, codename, layout):
    version = os.environ.get('BEYOUD_ALPHA_VERSION')
    if version is not None and not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*', version):
        raise ValueError('BEYOUD_ALPHA_VERSION must be numeric dot-separated components, such as 3.2')
    run_number = _positive_env('GITHUB_RUN_NUMBER')
    run_attempt = _positive_env('GITHUB_RUN_ATTEMPT')
    run_id = os.environ.get('GITHUB_RUN_ID')
    repository = os.environ.get('GITHUB_REPOSITORY')
    server = os.environ.get('GITHUB_SERVER_URL', 'https://github.com').rstrip('/')
    run_url = f'{server}/{repository}/actions/runs/{run_id}' if repository and run_id else None
    return {
        'project': 'X-NovaOS',
        'version': f'Alpha {version}' if version else None,
        'alpha_version': version,
        'build_number': run_number,
        'run_attempt': run_attempt,
        'target_model': model,
        'target_codename': codename,
        'partition_layout': layout,
        'format': 'raw-images-only-v1',
        'automatic_installer_included': False,
        'recovery_installer_included': False,
        'flashing_method_included': False,
        'hardware_validated': False,
        'release_published': False,
        'github_run_id': run_id,
        'github_run_url': run_url,
        'source_commit': os.environ.get('GITHUB_SHA'),
    }


def _validate_target_config(path, model, codename, environment):
    if path.is_symlink() or not path.is_file():
        raise ValueError('Missing/unsafe target partition configuration')
    text = path.read_text()
    codename_values = re.findall(r'^TARGET_CODENAME="([A-Za-z0-9_-]+)"\s*$', text, re.MULTILINE)
    model_arrays = re.findall(r'^TARGET_ASSERT_MODEL=\(([^)]*)\)\s*$', text, re.MULTILINE)
    super_values = re.findall(r'^TARGET_SUPER_PARTITION_SIZE="?([0-9]+)"?\s*$', text, re.MULTILINE)
    filesystem_values = re.findall(r'^TARGET_OS_FILE_SYSTEM="(ext4|erofs)"\s*$', text, re.MULTILINE)
    system_ext_values = re.findall(r'^TARGET_HAS_SYSTEM_EXT=(true|false)\s*$', text, re.MULTILINE)
    if (codename_values != [codename] or len(model_arrays) != 1
            or re.findall(r'"([A-Za-z0-9_-]+)"', model_arrays[0]) != [model]
            or super_values != ['0'] or len(filesystem_values) != 1
            or len(system_ext_values) != 1):
        raise ValueError('Target config does not prove the expected model and static S10 partition layout')
    asserted = set(re.findall(r'SM-[A-Z0-9]+', environment.get('TARGET_ASSERT_MODEL', '')))
    if asserted and asserted != {model}:
        raise ValueError('Build target model assertion differs from workspace marker/config')
    if environment.get('TARGET_CODENAME') != codename:
        raise ValueError('Build target environment does not match workspace marker')
    return {
        'filesystem': filesystem_values[0],
        'super_partition_size': 0,
        'has_system_ext': system_ext_values[0] == 'true',
    }


def _detect_filesystem(path):
    with path.open('rb') as stream:
        stream.seek(1024)
        if stream.read(4) == struct.pack('<I', EROFS_MAGIC):
            return 'erofs'
        stream.seek(1024 + 0x38)
        if stream.read(2) == b'\x53\xef':
            return 'ext4'
    return None


def _verify_kernel_image(name, path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size <= 0:
        raise ValueError(f'Missing/unsafe kernel image: {name}.img')
    with path.open('rb') as stream:
        header = stream.read(8)
    if len(header) < 4:
        raise ValueError(f'Truncated kernel image: {name}.img')
    if struct.unpack('<I', header[:4])[0] == SPARSE_MAGIC:
        raise ValueError(f'Kernel image must be a raw .img, not sparse: {name}.img')
    if name in {'boot', 'init_boot', 'vendor_boot'} and not header.startswith(b'ANDROID!'):
        raise ValueError(f'Invalid Android boot image: {name}.img')
    if name == 'dtbo' and header[:4] != bytes.fromhex('d7b7ab1e'):
        raise ValueError('Invalid DTBO image')
    if name == 'dtb' and header[:4] != bytes.fromhex('d00dfeed'):
        raise ValueError('Invalid device-tree blob image')
    return {'status': 'raw-header-verified', 'format': name, 'bytes': path.stat().st_size}


def build(workspace):
    """Create/verify the RAW image staging directory used by the TWRP ZIP step."""
    workspace = Path(workspace).resolve()
    marker_path = workspace / 'BEYOUD-WORKSPACE.json'
    if marker_path.is_symlink() or not marker_path.is_file():
        raise ValueError('Missing/unsafe generated workspace marker')
    marker = json.loads(marker_path.read_text())
    codename, device = from_marker(marker)
    model = device['model']
    if (codename, model) != ('beyond1lte', 'SM-G973F'):
        raise ValueError('The audited raw-image output currently supports only SM-G973F / beyond1lte')

    output_format = os.environ.get('BEYOUD_OUTPUT_FORMAT', 'twrp-zip')
    if output_format != 'twrp-zip':
        raise ValueError('RAW images are an internal staging format for the TWRP-installable ROM ZIP')
    target_config = workspace / 'target' / codename / 'config.sh'
    if any(path.is_symlink() for path in (workspace / 'target', target_config.parent, target_config)):
        raise ValueError('Target configuration must not traverse symlinked paths')
    target_layout = _validate_target_config(target_config, model, codename, os.environ)
    super_size = target_layout['super_partition_size']
    if super_size != 0:
        raise ValueError('Raw image-only mode currently requires the S10 static partition layout (no super image)')

    out = workspace / 'out'
    if out.is_symlink() or not out.is_dir():
        raise ValueError('Unsafe/missing workspace out directory')
    raw_root = out / 'raw-images'
    if raw_root.is_symlink() or (raw_root.exists() and not raw_root.is_dir()):
        raise ValueError('Unsafe raw image output directory')
    raw_root.mkdir(exist_ok=True)
    destination = raw_root / codename
    if destination.exists() or destination.is_symlink():
        raise ValueError('Refusing to replace an existing raw image bundle')

    work_path = out / 'target' / codename / 'work_dir'
    target_root = out / 'target'
    target_device = target_root / codename
    if any(path.is_symlink() for path in (target_root, target_device, work_path)):
        raise ValueError('Target work tree must not contain symlinked path components')
    expected_work = work_path.resolve(strict=True)
    if not expected_work.is_relative_to(workspace):
        raise ValueError('Target work tree resolves outside the generated workspace')
    work_value = os.environ.get('WORK_DIR')
    if not work_value or Path(work_value).resolve() != expected_work:
        raise ValueError('WORK_DIR does not resolve to the verified S10 target work tree')
    work = expected_work
    kernel = work / 'kernel'
    configs = work / 'configs'
    image_builder = workspace / 'scripts/build_fs_image.sh'
    if not work.is_dir() or kernel.is_symlink() or not kernel.is_dir():
        raise ValueError('Missing/unsafe work or kernel image directory')
    if configs.is_symlink() or not configs.is_dir():
        raise ValueError('Missing/unsafe filesystem metadata directory')
    if (workspace / 'scripts').is_symlink() or image_builder.is_symlink() or not image_builder.is_file():
        raise ValueError('Pinned Artisan filesystem image builder is missing')

    inputs = load_package_inputs(workspace)
    if inputs.get('codename') != codename or inputs.get('model') != model:
        raise ValueError('Package input identity does not match selected target')
    layout = inputs.get('partition_layout', {}).get('id', 'stock')
    caps = image_caps(inputs)
    filesystem = target_layout['filesystem']

    partitions = []
    for name in FILESYSTEM_ORDER:
        path = work / name
        if path.is_symlink():
            raise ValueError(f'Partition tree must not be a symlink: {name}')
        if path.exists():
            if not path.is_dir():
                raise ValueError(f'Partition tree is not a directory: {name}')
            if name not in caps:
                raise ValueError(f'No audited physical image-size profile for partition: {name}')
            partitions.append(name)
    if not REQUIRED_FILESYSTEM <= set(partitions):
        raise ValueError(f'Missing required filesystem partition trees: {sorted(REQUIRED_FILESYSTEM - set(partitions))}')
    if 'system_ext' in partitions and not target_layout['has_system_ext']:
        raise ValueError('S10 config embeds system_ext inside system; separate system_ext.img is not an audited target partition')
    if target_layout['has_system_ext'] and 'system_ext' not in partitions:
        raise ValueError('Target config declares a separate system_ext partition but no image tree was built')

    kernel_images = {}
    for name in KERNEL_ORDER:
        path = kernel / f'{name}.img'
        if path.is_symlink():
            raise ValueError(f'Kernel image must not be a symlink: {name}.img')
        if path.is_file():
            kernel_images[name] = path
    for path in kernel.glob('*.img'):
        if path.stem not in KERNEL_ORDER:
            raise ValueError(f'Unsupported kernel image role; review before distribution: {path.name}')
    if not REQUIRED_KERNEL <= set(kernel_images):
        raise ValueError(f'Missing required boot component images: {sorted(REQUIRED_KERNEL - set(kernel_images))}')

    temp = Path(tempfile.mkdtemp(prefix=f'.{codename}.raw-build-', dir=raw_root))
    records = []
    proof_file = None
    proof_partial = None
    proof_attempted = False
    destination_created = False
    try:
        for name in partitions:
            tree = work / name
            file_context = configs / f'file_context-{name}'
            fs_config = configs / f'fs_config-{name}'
            for path in (file_context, fs_config):
                if path.is_symlink() or not path.is_file():
                    raise ValueError(f'Missing/unsafe image metadata for {name}: {path.name}')
            built = temp / f'.build-{name}.img'
            output = temp / f'{name}.img'
            image_fs = 'ext4' if name in {'system', 'vendor', 'prism', 'optics'} else filesystem
            command = [str(image_builder), image_fs, '-o', str(built), '-S', str(tree),
                       str(file_context), str(fs_config)]
            print(f'Building raw filesystem image {name}.img ({image_fs})', flush=True)
            subprocess.run(command, cwd=workspace, env=os.environ.copy(), check=True)
            if built.is_symlink() or not built.is_file() or built.stat().st_size <= 0:
                raise ValueError(f'Filesystem image builder produced no valid {name}.img')
            with built.open('rb') as stream:
                sparse = stream.read(4) == struct.pack('<I', SPARSE_MAGIC)
            if sparse:
                subprocess.run(['simg2img', str(built), str(output)], cwd=workspace,
                               env=os.environ.copy(), check=True)
                built.unlink()
            else:
                os.replace(built, output)
            if output.is_symlink() or not output.is_file() or output.stat().st_size <= 0:
                raise ValueError(f'Raw image conversion produced no valid {name}.img')
            report = verify_image(output)
            if report.get('sparse') or report.get('status') != 'filesystem-verified':
                raise ValueError(f'Filesystem image was not verified as an expanded raw image: {name}.img')
            logical_bytes = output.stat().st_size
            cap = caps[name]
            if type(cap) is int and logical_bytes > cap:
                raise ValueError(f'{name}.img size {logical_bytes} exceeds physical image capacity {cap}')
            records.append({
                'name': name, 'filename': output.name, 'role': 'filesystem-partition',
                'bytes': logical_bytes, 'sha256': sha256(output),
                'filesystem': report['filesystem'], 'sparse': False,
            })

        for name in KERNEL_ORDER:
            source = kernel_images.get(name)
            if source is None:
                continue
            output = temp / f'{name}.img'
            shutil.copyfile(source, output)
            kernel_report = _verify_kernel_image(name, output)
            records.append({
                'name': name, 'filename': output.name, 'role': 'boot-component',
                'bytes': output.stat().st_size, 'sha256': sha256(output),
                'filesystem': None, 'sparse': False, 'validation': kernel_report['status'],
            })

        records.sort(key=lambda item: IMAGE_ORDER.index(item['name']))
        names = {item['name'] for item in records}
        if not REQUIRED_IMAGES <= names:
            raise ValueError(f'Final raw bundle is missing required images: {sorted(REQUIRED_IMAGES - names)}')

        info = _build_identity(model, codename, layout)
        info['image_count'] = len(records)
        non_image_sources = list(work.iterdir()) + list(kernel.iterdir())
        info['excluded_non_image_components'] = sorted({
            path.name for path in non_image_sources
            if path.is_file() and path.name == 'up_param.bin'
        })
        lock = out / 'firmware-lock.json'
        if lock.is_symlink() or not lock.is_file():
            raise ValueError('Verified firmware lock is missing/unsafe')
        proof_root = workspace / PROOF_ROOT
        if proof_root.is_symlink() or (proof_root.exists() and not proof_root.is_dir()):
            raise ValueError('Unsafe raw image proof directory')
        proof_root.mkdir(parents=True, exist_ok=True)
        proof_file = proof_root / f'{codename}.json'
        proof_partial = proof_file.with_suffix('.partial')
        if (proof_file.exists() or proof_file.is_symlink()
                or proof_partial.exists() or proof_partial.is_symlink()):
            raise ValueError('Refusing to replace existing raw image proof data')
        receipt = {
            'schema_version': 1,
            'format': 'raw-images-only-v1',
            'status': 'images-built-and-host-verified',
            'target_model': model,
            'target_codename': codename,
            'partition_layout': layout,
            'required_images': [name for name in IMAGE_ORDER if name in REQUIRED_IMAGES],
            'contains_recovery': False,
            'contains_installer': False,
            'contains_new_dat_br': False,
            'contains_transfer_lists': False,
            'firmware_lock_sha256': sha256(lock),
            'build': info,
            'provenance': marker,
            'images': records,
        }
        final = {
            'status': 'raw-images-built-and-host-verified',
            'target_model': model,
            'target_codename': codename,
            'images': records,
        }
        # The public bundle is deliberately flat and contains ONLY .img files.
        # Build identity, provenance, and checksums remain outside that bundle.
        verify_bundle(temp, model, codename, receipt=receipt, verify_hashes=True)
        proof_attempted = True
        atomic_json(proof_file, receipt)
        temp.rename(destination)
        temp = None
        destination_created = True
        print(json.dumps(final, indent=2), flush=True)
        return destination
    except BaseException:
        if temp is not None:
            shutil.rmtree(temp, ignore_errors=True)
        if destination_created:
            shutil.rmtree(destination, ignore_errors=True)
        if proof_attempted and proof_file is not None:
            proof_file.unlink(missing_ok=True)
        if proof_partial is not None and not proof_partial.is_symlink():
            proof_partial.unlink(missing_ok=True)
        raise


def verify_bundle(bundle, expected_model=None, expected_codename=None, receipt=None,
                  verify_hashes=False):
    """Validate an image-only directory against an external build receipt."""
    bundle = Path(bundle)
    if bundle.is_symlink() or not bundle.is_dir():
        raise ValueError('Raw image bundle is missing or unsafe')
    receipt_supplied_as_path = isinstance(receipt, (str, Path))
    if receipt_supplied_as_path:
        receipt_path = Path(receipt)
        if receipt_path.is_symlink() or not receipt_path.is_file():
            raise ValueError('Raw image build receipt is missing or unsafe')
        receipt = json.loads(receipt_path.read_text())
    if not isinstance(receipt, dict):
        raise ValueError('An external raw image build receipt is required')

    entries = list(bundle.iterdir())
    if any(path.is_symlink() or not path.is_file() for path in entries):
        raise ValueError('Raw image bundle must be flat and contain only regular files')
    if not entries or any(path.suffix != '.img' or path.name != f'{path.stem}.img' for path in entries):
        raise ValueError('The deliverable directory must contain .img files only')
    files = {path.stem: path for path in entries}
    if len(files) != len(entries) or set(files) - set(IMAGE_ORDER):
        raise ValueError('Raw image bundle contains duplicate or unsupported image roles')
    if not REQUIRED_IMAGES <= set(files):
        raise ValueError(f'Missing required raw images: {sorted(REQUIRED_IMAGES - set(files))}')

    if (receipt.get('schema_version') != 1 or receipt.get('format') != 'raw-images-only-v1'
            or receipt.get('status') != 'images-built-and-host-verified'):
        raise ValueError('Unsupported or incomplete raw image build receipt')
    model = receipt.get('target_model')
    codename = receipt.get('target_codename')
    if expected_model is not None and model != expected_model:
        raise ValueError('Raw image bundle model mismatch')
    if expected_codename is not None and codename != expected_codename:
        raise ValueError('Raw image bundle codename mismatch')
    if receipt.get('required_images') != [name for name in IMAGE_ORDER if name in REQUIRED_IMAGES]:
        raise ValueError('Raw image receipt has an unexpected required-image map')
    for key in ('contains_recovery', 'contains_installer', 'contains_new_dat_br',
                'contains_transfer_lists'):
        if receipt.get(key) is not False:
            raise ValueError(f'{key} must be false in the raw-images-only receipt')
    lock_digest = receipt.get('firmware_lock_sha256')
    if not isinstance(lock_digest, str) or not re.fullmatch(r'[0-9a-f]{64}', lock_digest):
        raise ValueError('Raw image receipt has no verified firmware-lock digest')

    records = receipt.get('images')
    if not isinstance(records, list) or not records:
        raise ValueError('Raw image receipt has no image records')
    record_names = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('Malformed raw image receipt record')
        name = record.get('name')
        filename = record.get('filename')
        if name not in IMAGE_ORDER or filename != f'{name}.img' or name in record_names:
            raise ValueError(f'Unexpected/duplicate raw image role: {name}')
        record_names.append(name)
        path = files.get(name)
        if path is None:
            raise ValueError(f'Missing raw image: {filename}')
        size = path.stat().st_size
        if type(record.get('bytes')) is not int or size <= 0 or record.get('bytes') != size:
            raise ValueError(f'Raw image size mismatch: {filename}')
        if record.get('sparse') is not False:
            raise ValueError(f'Raw image must be expanded, not sparse: {filename}')
        digest = record.get('sha256')
        if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError(f'Raw image receipt has an invalid SHA-256: {filename}')
        if (verify_hashes or receipt_supplied_as_path) and sha256(path) != digest:
            raise ValueError(f'Raw image SHA-256 mismatch: {filename}')
        if name in FILESYSTEM_ORDER:
            with path.open('rb') as stream:
                sparse = stream.read(4) == struct.pack('<I', SPARSE_MAGIC)
            if (sparse or record.get('role') != 'filesystem-partition'
                    or record.get('filesystem') not in {'ext4', 'erofs'}
                    or _detect_filesystem(path) != record.get('filesystem')):
                raise ValueError(f'Filesystem image signature/sparse-format mismatch: {filename}')
        else:
            if (record.get('role') != 'boot-component'
                    or record.get('filesystem') is not None
                    or record.get('validation') != 'raw-header-verified'):
                raise ValueError(f'Invalid boot-component receipt: {filename}')
            _verify_kernel_image(name, path)
    if record_names != [name for name in IMAGE_ORDER if name in files]:
        raise ValueError('Raw image receipt is not in canonical partition order')
    if set(record_names) != set(files):
        raise ValueError('Raw image receipt does not describe exactly the delivered images')

    build = receipt.get('build')
    if (not isinstance(build, dict) or build.get('project') != 'X-NovaOS'
            or build.get('format') != 'raw-images-only-v1'
            or build.get('target_model') != model or build.get('target_codename') != codename
            or build.get('partition_layout') != receipt.get('partition_layout')
            or build.get('automatic_installer_included') is not False
            or build.get('recovery_installer_included') is not False
            or build.get('flashing_method_included') is not False
            or build.get('hardware_validated') is not False
            or build.get('image_count') != len(records)):
        raise ValueError('Raw image build identity does not match the receipt')
    if expected_model is not None and build.get('target_model') != expected_model:
        raise ValueError('Build metadata model mismatch')
    if expected_codename is not None and build.get('target_codename') != expected_codename:
        raise ValueError('Build metadata codename mismatch')
    provenance = receipt.get('provenance')
    if not isinstance(provenance, dict):
        raise ValueError('Raw image receipt has no workspace provenance marker')
    marked_codename, device = from_marker(provenance)
    if marked_codename != codename or device['model'] != model:
        raise ValueError('Raw image provenance target does not match the receipt')

    ordered_names = [name for name in IMAGE_ORDER if name in files]
    return {
        'status': 'raw-images-verified',
        'target_model': model,
        'target_codename': codename,
        'images': ordered_names,
        'image_count': len(ordered_names),
        'raw_image_bytes': sum(files[name].stat().st_size for name in ordered_names),
        'sha256': {name: receipt['images'][index]['sha256'] for index, name in enumerate(record_names)},
        'build_number': build.get('build_number'),
        'run_attempt': build.get('run_attempt'),
        'hardware_validated': False,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace', type=Path)
    parser.add_argument('--verify-only', action='store_true', help='Validate an existing raw-image bundle')
    args = parser.parse_args()
    try:
        if args.verify_only:
            marker = json.loads((args.workspace / 'BEYOUD-WORKSPACE.json').read_text())
            codename, device = from_marker(marker)
            result = verify_bundle(
                args.workspace / 'out/raw-images' / codename,
                expected_model=device['model'], expected_codename=codename,
                receipt=args.workspace / PROOF_ROOT / f'{codename}.json',
                verify_hashes=True,
            )
        else:
            result = {'bundle': str(build(args.workspace)), 'status': 'raw-images-built-and-host-verified'}
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f'Raw image build/validation stopped: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
