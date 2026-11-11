#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Project-maintained, fail-closed S10 compatibility checks and workspace edits."""
import argparse
from pathlib import Path
import re
import shutil
import sys

try:
    from .targets import TARGETS
except ImportError:
    # The same file is also invoked as a standalone workspace utility.
    from targets import TARGETS

ROOT = Path(__file__).resolve().parents[1]
APEX_IMPORT = 'ADD_TO_WORK_DIR "b0sxxx" "system" "system/apex/com.android.bt.apex" 0 0 644 "u:object_r:system_file:s0"'
BT_PATCH_TAILS = (
    '    "289767394805003736008052" "289767392a00001436008052"',
    '    "289765394805003736008052" "289765392a00001436008052"',
)
SOURCE_SDK_GATE = 'if [[ "$SOURCE_API_LEVEL" -lt 37 ]]; then'
DONOR_SDK_GATE = 'if (( _BEYOUD_DONOR_SDK < 37 )); then'
BT_PATCH_PREFIX = 'HEX_PATCH "$WORK_DIR/system/system/lib64/libbluetooth_jni.so" ' + chr(92) + '\n'
LEGACY_MODULE = Path('platform/exynos9820/patches/zz_xnova_legacy_init')


def _checked(root, relative):
    root = Path(root).resolve(strict=True)
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
        raise ValueError(f'Missing or unsafe compatibility input: {relative}')
    return path


def donor_sdk(firmwares, descriptor):
    """Read the SDK from the staged donor, never from its declarative profile."""
    parts = descriptor.split('/')
    if (len(parts) not in (2, 3)
            or not re.fullmatch(r'SM-[A-Z0-9]+', parts[0])
            or not re.fullmatch(r'[A-Z0-9]+', parts[1])
            or (len(parts) == 3 and not re.fullmatch(r'[A-Z0-9]+', parts[2]))):
        raise ValueError('Invalid source firmware descriptor')
    prop = _checked(firmwares, f'{parts[0]}_{parts[1]}/system/system/build.prop')
    values = [line.partition('=')[2].strip() for line in prop.read_text().splitlines()
              if line.partition('=')[0].strip() == 'ro.build.version.sdk']
    if len(values) != 1 or not re.fullmatch(r'[0-9]+', values[0]):
        raise ValueError('Expected exactly one valid SDK in the extracted donor build.prop')
    sdk = int(values[0])
    if not 1 <= sdk <= 1000:
        raise ValueError('Donor SDK is outside the supported numeric range')
    return sdk


def guard_legacy_bluetooth(text):
    """Gate both pinned Artisan/OneROM Bluetooth schemas on the extracted donor SDK."""
    if text.count(APEX_IMPORT) != 1 or text.count('# BT-lib-patch\n') != 1:
        raise ValueError('Unexpected S10 Bluetooth patch anchors')
    tails = [tail for tail in BT_PATCH_TAILS if text.count(BT_PATCH_PREFIX + tail) == 1]
    if len(tails) != 1:
        raise ValueError('Unexpected or ambiguous S10 Bluetooth byte-patch command')
    tail = tails[0]
    patch_command = BT_PATCH_PREFIX + tail
    probe = ('_BEYOUD_DONOR_SDK=$(python3 "$SRC_DIR/integration/s10_compat.py" '
             'sdk "$FW_DIR" "$SOURCE_FIRMWARE") || return 1\n')
    source_gates = text.count(SOURCE_SDK_GATE)
    if source_gates == 0:
        # Artisan's pinned customization has unconditional anchors. Wrap only
        # the two legacy operations, leaving every other customization intact.
        gated_apex = (probe + DONOR_SDK_GATE + '\n    ' + APEX_IMPORT + '\nfi')
        text = text.replace(APEX_IMPORT, gated_apex, 1)
        guarded_patch = (DONOR_SDK_GATE + '\n' + patch_command + '\nfi\n'
                         'unset _BEYOUD_DONOR_SDK')
        return text.replace(patch_command, guarded_patch, 1)
    if source_gates != 2:
        raise ValueError('Unexpected OneROM Bluetooth SDK-gate schema')
    first_gate = text.index(SOURCE_SDK_GATE)
    second_gate = text.index(SOURCE_SDK_GATE, first_gate + len(SOURCE_SDK_GATE))
    apex_at = text.index(APEX_IMPORT)
    tail_at = text.index(tail)
    if not (first_gate < apex_at < second_gate < tail_at):
        raise ValueError('OneROM Bluetooth gates no longer enclose the expected operations')
    text = text.replace(SOURCE_SDK_GATE, DONOR_SDK_GATE)
    text = text[:first_gate] + probe + text[first_gate:]
    tail_end = text.index(tail) + len(tail)
    outer_close = text.find('\nfi', tail_end)
    if outer_close < 0:
        raise ValueError('OneROM Bluetooth patch gate is unterminated')
    close_end = outer_close + len('\nfi')
    return text[:close_end] + '\nunset _BEYOUD_DONOR_SDK' + text[close_end:]


def initialize_legacy_vendor(work):
    """Merge only the two checked legacy vendor-init declarations, idempotently."""
    root = Path(work).resolve(strict=True)
    ueventd = _checked(root, 'system/system/etc/ueventd.rc')
    vendor_rc = _checked(root, 'vendor/ueventd.rc')
    contexts = _checked(root, 'vendor/etc/selinux/vendor_property_contexts')
    policy = _checked(root, 'vendor/etc/selinux/vendor_sepolicy.cil')
    del vendor_rc  # Presence is required so the imported path resolves on-device.

    system_text = ueventd.read_text()
    context_text = contexts.read_text()
    policy_text = policy.read_text()
    if '\0' in system_text or '\0' in context_text or '\0' in policy_text:
        raise ValueError('Unexpected binary vendor-init input')

    imports = [line for line in system_text.splitlines()
               if re.match(r'^\s*import\s+/vendor/ueventd\.rc(?:\s*(?:#.*)?)$', line)]
    if len(imports) > 1:
        raise ValueError('Duplicate system import for the vendor ueventd rules')
    if imports:
        next_system = system_text
    else:
        separator = '' if not system_text or system_text.endswith('\n') else '\n'
        next_system = system_text + separator + 'import /vendor/ueventd.rc\n'

    rild_entries = [line for line in context_text.splitlines()
                    if line.split('#', 1)[0].strip().split()[:1] == ['vendor.sec.rild.libpath']]
    if len(rild_entries) > 1:
        raise ValueError('Ambiguous RIL property context entries')
    next_context = context_text
    if not rild_entries and re.search(r'^\s*\(type\s+vendor_rild_prop\s*\)', policy_text, re.M):
        separator = '' if not context_text or context_text.endswith('\n') else '\n'
        next_context = context_text + separator + 'vendor.sec.rild.libpath u:object_r:vendor_rild_prop:s0\n'
    elif context_text and not context_text.endswith('\n'):
        next_context += '\n'

    # Validate both output strings before changing either input.
    if next_system != system_text:
        ueventd.write_text(next_system)
    if next_context != context_text:
        contexts.write_text(next_context)


def install(workspace, codename):
    if codename not in TARGETS:
        raise ValueError('Unsupported S10 workspace target')
    workspace = Path(workspace).resolve(strict=True)
    customize = workspace / 'platform/exynos9820/patches/miscs/customize.sh'
    if customize.is_symlink() or not customize.is_file():
        raise ValueError('Missing or unsafe S10 miscs customization script')
    updated = guard_legacy_bluetooth(customize.read_text())
    destination = workspace / LEGACY_MODULE
    if destination.exists() or destination.is_symlink():
        raise ValueError('Refusing to overwrite an existing S10 compatibility module')

    destination.mkdir(parents=True)
    try:
        (destination / 'module.prop').write_text(
            'id=xnova_s10_legacy_init\n'
            'name=X-Nova S10 legacy vendor initialization\n'
            'version=1\n'
            'versionCode=1\n'
            'author=X-Nova OS contributors\n'
            'description=Checked import of stock vendor ueventd and RIL property context.\n'
        )
        (destination / 'customize.sh').write_text(
            '# SPDX-License-Identifier: GPL-3.0-or-later\n'
            'SKIPUNZIP=1\n'
            'python3 "$SRC_DIR/integration/s10_compat.py" init "$WORK_DIR" || return 1\n'
        )
        customize.write_text(updated)
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return {
        'target': codename,
        'active': ['SDK < 37 donor-gated S10 Bluetooth path', 'checked vendor-init compatibility'],
        'disabled_candidates': [],
        'boot_validated': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    sdk = commands.add_parser('sdk')
    sdk.add_argument('firmwares', type=Path)
    sdk.add_argument('descriptor')
    init = commands.add_parser('init')
    init.add_argument('work', type=Path)
    args = parser.parse_args()
    if args.command == 'sdk':
        print(donor_sdk(args.firmwares, args.descriptor))
    else:
        initialize_legacy_vendor(args.work)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f'S10 compatibility stage blocked: {exc}', file=sys.stderr)
        sys.exit(1)
