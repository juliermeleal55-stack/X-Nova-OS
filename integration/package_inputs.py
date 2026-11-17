#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Preserve verified package inputs and partition profiles before firmware retirement."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import struct
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integration.samloader.metadata import configured_firmwares, get
from integration.targets import from_marker


EXTREME_STRUCTURE_PARTITIONS = ('system', 'vendor', 'product', 'odm', 'prism', 'optics')
EXTREME_STRUCTURE_BOOT_COMPONENTS = ('dtb', 'dtbo', 'boot')
EXTREME_STRUCTURE_PAYLOAD_FORMAT = 'expanded-raw-img-in-s10-twrp-zip'
EXTREME_STRUCTURE_REFERENCE_SCOPE = 'partition-names-only; no physical-layout or ArtisanROM-equivalence claim'
EXTREME_STRUCTURE_PAYLOAD_FORMAT_SOURCE = 'existing-s10-twrp-raw-image-pipeline; not attributed to ExtremeROM'
EXTREME_REPARTITIONER_PARTITIONS = (
    'system', 'vendor', 'product', 'odm', 'prism', 'optics', 'cache', 'omr',
    'cp_debug', 'cp2_debug', 'spu', 'userdata',
)


def _workspace_target(workspace):
    marker = json.loads((workspace / 'BEYOUD-WORKSPACE.json').read_text())
    return from_marker(marker)


def _extreme_structure_profile(workspace):
    codename, device = _workspace_target(workspace)
    if (device['model'], codename) != ('SM-G975F', 'beyond2lte'):
        raise ValueError('ExtremeROM structure-only profile is scoped to SM-G975F/beyond2lte')
    if os.environ.get('BEYOUD_OUTPUT_FORMAT', 'twrp-zip') != 'twrp-zip':
        raise ValueError('ExtremeROM structure-only profile requires the existing S10 TWRP ZIP pipeline')
    path = Path(__file__).resolve().parent / 'partition_layouts/extreme-structure-beyond2lte.json'
    if path.is_symlink() or not path.is_file():
        raise ValueError('Pinned ExtremeROM structure profile is missing/unsafe')
    raw = path.read_bytes()
    profile = json.loads(raw)
    if (profile.get('schema_version') != 1
            or profile.get('id') != 'extreme-structure'
            or profile.get('model') != device['model']
            or profile.get('codename') != codename
            or profile.get('image_partitions') != list(EXTREME_STRUCTURE_PARTITIONS)
            or profile.get('boot_components') != list(EXTREME_STRUCTURE_BOOT_COMPONENTS)
            or profile.get('repartitioner_partitions') != list(EXTREME_REPARTITIONER_PARTITIONS)
            or profile.get('reference_scope') != EXTREME_STRUCTURE_REFERENCE_SCOPE
            or profile.get('payload_format') != EXTREME_STRUCTURE_PAYLOAD_FORMAT
            or profile.get('payload_format_source') != EXTREME_STRUCTURE_PAYLOAD_FORMAT_SOURCE
            or 'image_size_caps' in profile):
        raise ValueError('ExtremeROM structure profile is malformed or contains fixed size limits')
    return {
        'id': profile['id'],
        'sha256': hashlib.sha256(raw).hexdigest(),
        'requires': profile['requires'],
        'reference_scope': profile['reference_scope'],
        'payload_format': profile['payload_format'],
        'payload_format_source': profile['payload_format_source'],
        'image_partitions': profile['image_partitions'],
        'boot_components': profile['boot_components'],
        'repartitioner_partitions': profile['repartitioner_partitions'],
    }


def selected_layout(workspace):
    name = os.environ.get('BEYOUD_PARTITION_LAYOUT', 'stock')
    if name == 'stock':
        return dict(id='stock', sha256=None)
    if name == 'content-sized':
        codename, device = _workspace_target(workspace)
        if (device['model'], codename) not in {('SM-G973F', 'beyond1lte'), ('SM-G975F', 'beyond2lte')}:
            raise ValueError('Content-sized layout is scoped to the audited Exynos S10/S10+ candidates')
        return dict(
            id=name,
            sha256=None,
            requires='Owner-managed repartition sized AFTER image generation; no fixed capacity promise; no automatic repartition.',
            image_size_caps=dict.fromkeys(EXTREME_STRUCTURE_PARTITIONS),
        )
    if name == 'extreme-structure':
        return _extreme_structure_profile(workspace)
    if name != 'extreme-default':
        raise ValueError('Unknown explicit partition layout')
    codename, device = _workspace_target(workspace)
    if (device['model'], codename) != ('SM-G973F', 'beyond1lte'):
        raise ValueError('Fixed-size ExtremeROM Default profile is disabled for beyond2lte; use extreme-structure')
    path = Path(__file__).resolve().parent / 'partition_layouts/extreme-default.json'
    if path.is_symlink() or not path.is_file():
        raise ValueError('Pinned ExtremeROM Default size profile is missing/unsafe')
    raw = path.read_bytes()
    profile = json.loads(raw)
    if (profile.get('schema_version') != 1 or profile.get('id') != name or profile.get('unit') != 'bytes'
            or profile.get('model') != device['model'] or profile.get('codename') != codename):
        raise ValueError('Fixed-size partition profile does not match selected S10 model')
    caps = profile.get('image_size_caps')
    if (set(caps or {}) != set(EXTREME_STRUCTURE_PARTITIONS)
            or any(type(value) is not int or value <= 0 or value % 1048576 for value in caps.values())):
        raise ValueError('Invalid declared partition profile capacities')
    return dict(
        id=name,
        sha256=hashlib.sha256(raw).hexdigest(),
        requires=profile['requires'],
        image_size_caps=caps,
    )


def _content_sized_caps(stock_caps):
    # The selected structure covers the six static S10 filesystem partitions.
    # Kernel modules/system_ext are not invented: they are enabled only when
    # the locked target firmware explicitly contains that partition.
    names = set(EXTREME_STRUCTURE_PARTITIONS)
    names.update(name for name in ('system_ext', 'vendor_dlkm', 'odm_dlkm', 'system_dlkm')
                 if name in stock_caps)
    return {name: None for name in names}


def _layout_image_caps(layout, stock_caps):
    if layout.get('id') in {'content-sized', 'extreme-structure'}:
        return _content_sized_caps(stock_caps)
    return layout.get('image_size_caps', stock_caps)


def image_caps(data):
    return data.get('image_size_caps', data['stock_image_size_caps'])


def lock_digest(workspace):
    return hashlib.sha256((workspace / 'out/firmware-lock.json').read_bytes()).hexdigest()


def atomic_json(path, data):
    temporary = path.with_suffix('.partial')
    with temporary.open('w') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def read_prop(path, key, aliases=(), fingerprint_keys=()):
    """Resolve real firmware properties, never invent a device from a model name.

    Malformed/duplicate preferred properties are errors, not reasons to fall
    through to another key. Android partition-scoped aliases are used only
    when the legacy property is absent.
    """
    props = {}
    for line in path.read_text().splitlines():
        if line.lstrip().startswith('#') or '=' not in line:
            continue
        name, _, value = line.partition('=')
        props.setdefault(name.strip(), []).append(value.strip())
    for name in (key, *aliases):
        if name not in props:
            continue
        values = props[name]
        if len(values) != 1 or not re.fullmatch(r'[A-Za-z0-9_.-]+', values[0]):
            raise ValueError(f'Invalid/ambiguous package identifier {name} in {path}')
        return values[0]
    # A standard Android fingerprint is brand/product/device:release/id/
    # incremental:type/tags. Only its device component is an equivalent here.
    token = r'[A-Za-z0-9_.-]+'
    pattern = rf'{token}/{token}/({token}):{token}/{token}/{token}:{token}/{token}'
    for name in fingerprint_keys:
        if name not in props:
            continue
        values = props[name]
        match = re.fullmatch(pattern, values[0]) if len(values) == 1 else None
        if not match:
            raise ValueError(f'Invalid/ambiguous firmware fingerprint {name} in {path}')
        return match.group(1)
    tried = ', '.join((key, *aliases, *fingerprint_keys))
    raise ValueError(f'Missing package identifier in {path}; tried {tried}')


def capture(workspace):
    codename, device = from_marker(json.loads((workspace / 'BEYOUD-WORKSPACE.json').read_text()))
    descriptors = list(configured_firmwares(workspace / 'out/config.sh'))
    if len(descriptors) < 2:
        raise ValueError('Expected source and target descriptors')
    ids = {}
    for role, descriptor in zip(('source', 'target'), descriptors[:2]):
        model, csc, *_ = descriptor.split('/')
        record = get(workspace / 'out/firmware-lock.json', model, csc)
        if role == 'target' and model != device['model']:
            raise ValueError('Target firmware does not match selected device')
        root = workspace / 'out/fw' / f'{model}_{csc}'
        if root.is_symlink() or not root.resolve().is_relative_to(workspace.resolve()):
            raise ValueError('Unsafe extracted firmware root')
        if not (root / '.extracted').is_file() or (root / '.extracted').read_text().strip() != record['version']:
            raise ValueError('Package identifiers require the locked extracted firmware')
        for suffix, relative, key in [('product', 'system/system/build.prop', 'ro.build.product'),
                                      ('vendor', 'vendor/build.prop', 'ro.product.vendor.device')]:
            path = root / relative
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError('Unsafe firmware property path')
            aliases = ('ro.product.system.device', 'ro.product.device') if suffix == 'product' else ('ro.product.device',)
            fingerprints = ('ro.system.build.fingerprint', 'ro.build.fingerprint') if suffix == 'product' else ('ro.vendor.build.fingerprint',)
            ids[f'{role}_{suffix}'] = read_prop(path, key, aliases, fingerprints)
    target_model, target_csc, *_ = descriptors[1].split('/')
    metadata = workspace / 'out/fw' / f'{target_model}_{target_csc}' / 'os_partitions_metadata.txt'
    pairs = re.findall(r'^([a-z_]+)_size=([0-9]+)$', metadata.read_text(), re.M)
    limits = {name: int(size) for name, size in pairs}
    if len(limits) != len(pairs) or any(size <= 0 for size in limits.values()) or not {'system', 'vendor'} <= limits.keys():
        raise ValueError('Missing/ambiguous stock image size limits')
    layout=selected_layout(workspace)
    return dict(schema_version=1, codename=codename, model=device['model'],
                partition_layout=layout, image_size_caps=_layout_image_caps(layout,limits),
                firmware_lock_sha256=lock_digest(workspace), identifiers=ids,
                stock_image_size_caps=limits)


def load(workspace):
    cache = workspace / 'out/beyoud-package-inputs.json'
    data = json.loads(cache.read_text()) if cache.is_file() else capture(workspace)
    codename, device = from_marker(json.loads((workspace / 'BEYOUD-WORKSPACE.json').read_text()))
    if (data.get('schema_version') != 1 or data.get('codename') != codename or data.get('model') != device['model']
            or data.get('firmware_lock_sha256') != lock_digest(workspace)):
        raise ValueError('Package identifiers do not match workspace/firmware lock')
    if data.get('partition_layout',{'id':'stock','sha256':None}) != selected_layout(workspace):
        raise ValueError('Cached package inputs do not match selected partition layout')
    layout=selected_layout(workspace)
    expected_caps = _layout_image_caps(layout, data['stock_image_size_caps'])
    if image_caps(data) != expected_caps:
        raise ValueError('Cached image capacities differ from selected layout')
    return data


def write_layout_check(workspace, destination):
    data = load(workspace)
    if destination.is_symlink() or destination.parent.resolve() != (workspace / 'out/zip').resolve():
        raise ValueError('Unsafe recovery layout-check destination')
    script = '#!/sbin/sh\n# Read-only capacity check; never repartition or format.\n'
    layout = data.get('partition_layout', {}).get('id', 'stock')
    if layout != 'stock':
        script += (Path(__file__).resolve().parent / 'recovery_layout_check.sh').read_text() + '\n'
        caps = image_caps(data)
        if layout in {'content-sized', 'extreme-structure'}:
            report = json.loads((workspace / 'out/zip/REQUIRED-IMAGE-SIZES.json').read_text())
            caps = report.get('image_size_bytes', {})
            required = set(data['partition_layout'].get('image_partitions', ()))
            if layout == 'content-sized':
                required.add('system')
            if (report.get('layout') != layout or report.get('model') != data['model']
                    or report.get('partition_structure', []) != list(data['partition_layout'].get('image_partitions', ()))
                    or not required <= set(caps) or set(caps) - set(image_caps(data))
                    or any(type(value) is not int or value <= 0 for value in caps.values())):
                raise ValueError('Invalid generated image requirements')
        for name, cap in sorted(caps.items()):
            script += f'check_partition {name} {cap} || failures=1\n'
        script += 'log "Partition check complete: failures=$failures; details=$LOG"\nexit "$failures"\n'
    else:
        script += 'exit 0\n'
    destination.write_text(script)


def identifier(workspace, key):
    value = load(workspace)['identifiers'][key]
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', value):
        raise ValueError('Invalid cached package identifier')
    return value


def check_image(workspace, partition, image):
    data = load(workspace)
    layout = data.get('partition_layout', {}).get('id', 'stock')
    caps = image_caps(data)
    cap = caps.get(partition)
    unbounded = layout in {'content-sized', 'extreme-structure'}
    if partition not in caps or (not unbounded and (type(cap) is not int or cap <= 0)):
        raise ValueError(f'No selected image size cap for {partition}')
    with image.open('rb') as stream:
        header = stream.read(28)
    if len(header) >= 4 and struct.unpack('<I', header[:4])[0] == 0xED26FF3A:
        if len(header) != 28:
            raise ValueError('Truncated sparse image header')
        _, major, _, file_header, chunk_header, block, blocks, _, _ = struct.unpack('<I4H4I', header)
        if major != 1 or file_header < 28 or chunk_header < 12 or block <= 0 or block % 4 or blocks <= 0:
            raise ValueError('Invalid sparse image dimensions')
        logical = block * blocks
    else:
        logical = image.stat().st_size
    if logical <= 0 or (not unbounded and logical > cap):
        raise ValueError(f'{partition} logical image size={logical} exceeds selected image-size cap={cap}; revise payload, do not bypass')
    if unbounded:
        directory = workspace / 'out/zip'
        if directory.is_symlink():
            raise ValueError('Unsafe image requirements directory')
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / 'REQUIRED-IMAGE-SIZES.json'
        structure = list(data['partition_layout'].get('image_partitions', ()))
        if path.is_file():
            report = json.loads(path.read_text())
            if (report.get('layout') != layout or report.get('model') != data['model']
                    or report.get('partition_structure', []) != structure):
                raise ValueError('Existing image requirements belong to a different profile/target')
        else:
            report = {
                'layout': layout,
                'model': data['model'],
                'partition_structure': structure,
                'image_size_bytes': {},
            }
        report['image_size_bytes'][partition] = logical
        atomic_json(path, report)
    cap_text = 'none (no fixed build-time cap; not a device measurement)' if unbounded else f'{cap} bytes'
    print(f'{partition}: logical bytes={logical}, fixed build-time cap={cap_text}', flush=True)


def retire(workspace):
    workspace = workspace.resolve()
    out = workspace / 'out'
    fw = out / 'fw'
    tombstone = out / 'beyoud-fw-retired.json'
    if tombstone.exists():
        raise ValueError('Firmware retirement already started; resume at package after success, otherwise use a fresh workspace')
    if out.is_symlink() or fw.is_symlink() or fw.resolve().parent != out.resolve() or not fw.is_dir():
        raise ValueError('Unsafe firmware retirement root')
    descriptors = list(configured_firmwares(out / 'config.sh'))
    expected = set()
    for descriptor in descriptors:
        model, csc, *_ = descriptor.split('/')
        record = get(out / 'firmware-lock.json', model, csc)
        expected.add(f'{model}_{csc}')
        marker = fw / f'{model}_{csc}' / '.extracted'
        if marker.parent.is_symlink() or not marker.is_file() or marker.read_text().strip() != record['version']:
            raise ValueError('Cannot retire incomplete/mismatched firmware')
    if set(path.name for path in fw.iterdir()) != expected:
        raise ValueError('Unexpected firmware directories; refusing broad cleanup')
    mounts = Path('/proc/self/mountinfo')
    if not mounts.is_file():
        raise ValueError('Linux mount validation unavailable')
    for line in mounts.read_text().splitlines():
        mount = line.split()[4]
        for escaped, plain in [('\\040', ' '), ('\\011', '\t'), ('\\134', '\\')]:
            mount = mount.replace(escaped, plain)
        if Path(mount) == fw or fw in Path(mount).parents:
            raise ValueError('Refusing to delete mounted firmware')
    data = capture(workspace)
    atomic_json(out / 'beyoud-package-inputs.json', data)
    # Crash marker is written BEFORE destructive deletion. Earlier extraction
    # stages must never trust a half-deleted .extracted tree after interruption.
    atomic_json(tombstone, dict(status='retiring', firmware_lock_sha256=lock_digest(workspace)))
    shutil.rmtree(fw)
    atomic_json(tombstone, dict(status='retired', firmware_lock_sha256=lock_digest(workspace)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('get', 'verify', 'check-image', 'retire', 'layout-check'))
    parser.add_argument('workspace', type=Path)
    parser.add_argument('key', nargs='?')
    parser.add_argument('image', type=Path, nargs='?')
    args = parser.parse_args()
    if args.command == 'get':
        print(identifier(args.workspace, args.key))
    elif args.command == 'verify':
        for key in ('source_product', 'source_vendor', 'target_product', 'target_vendor'):
            identifier(args.workspace, key)
        print(json.dumps(load(args.workspace), indent=2))
    elif args.command == 'layout-check':
        write_layout_check(args.workspace, Path(args.key))
    elif args.command == 'check-image':
        check_image(args.workspace, args.key, args.image)
    else:
        retire(args.workspace)
