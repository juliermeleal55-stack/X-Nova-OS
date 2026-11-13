#!/usr/bin/env python3
"""Assemble a candidate Artisan S10 workspace, keeping heavy upstream files out of Git."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess
import tarfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integration.targets import DEFAULT_TARGET, TARGETS, select
from integration.build_policy import apply as apply_build_policy
from integration.framework_policy import install as install_framework
from integration.preflight_policy import install as install_preflight
from integration.runtime_paths import install as install_runtime_paths
from integration.onerom.install import install as install_onerom
from integration.onerom_port import import_onerom_sources
from integration.s10_compat import install as install_s10_compat

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = '5638a7f66cdf8bc9dd43f087a96f7dfa4f9e6954'
ARCHIVE_SHA256 = 'd755f75a19dc4adc7e0fc2b49553f6e5f03f0eefc69db1e7bb9baf0c7290c39e'
BASE_REPO = 'ArtisanROM-archive/ArtisanROM_old'


def check_archive(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    if digest.hexdigest() != ARCHIVE_SHA256:
        raise ValueError('Archive digest differs; do not extract or execute it')


def extract(path, destination):
    with tarfile.open(path, 'r:gz') as archive:
        prefix = f'ArtisanROM_old-{BASE_COMMIT}/'
        for member in archive:
            if member.name.rstrip('/') == prefix.rstrip('/'):
                continue
            if not member.name.startswith(prefix):
                raise ValueError('Unexpected archive root')
            member.name = member.name[len(prefix):]
            output = destination / member.name
            if not output.resolve().is_relative_to(destination.resolve()):
                raise ValueError('Unsafe archive member')
            if member.isdir():
                output.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                output.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as src, output.open('wb') as dst:
                    shutil.copyfileobj(src, dst)
                output.chmod(member.mode & 0o777)
            elif member.issym():
                # Android image trees contain absolute runtime symlinks.
                # Preserve them, but never follow them while extracting files.
                output.parent.mkdir(parents=True, exist_ok=True)
                output.symlink_to(member.linkname)
            else:
                raise ValueError('Unsupported archive member type')



def patch_downloader(workspace):
    path = workspace / 'scripts/download_fw.sh'
    text = path.read_text()
    old = 'samloader -m "$MODEL" -r "$CSC" -i "$IMEI" -s "$SERIAL_NO" download$STR -O "$ODIN_DIR/${MODEL}_${CSC}"'
    new = 'python3 "$SRC_DIR/integration/samloader/compat.py" -m "$MODEL" -r "$CSC" download -v "$LATEST_FIRMWARE" -O "$ODIN_DIR/${MODEL}_${CSC}"'
    if text.count(old) != 1:
        raise ValueError('Unexpected legacy downloader invocation')
    text = text.replace(old, new)
    text = text.replace('        #exit 1', '        exit 1')
    # Fail immediately on a rejected package, rather than retrying it eleven times.
    end = '        )\n\n        ZIP_FILE='
    if text.count(end) != 1:
        raise ValueError('Unexpected legacy download error handling')
    text = text.replace(end, '        ) || exit 1\n\n        ZIP_FILE=')
    text = text.replace('        STR=""\n        [ $MODEL == "SM-S731B" ] && STR=" -v S731BXXU1AYH9/S731BOXM1AYH9/S731BXXU1AYH9/S731BXXU1AYH9"\n', '')
    mkdir = '    mkdir -p "$ODIN_DIR/${MODEL}_${CSC}"'
    if mkdir in text:
        text = text.replace(mkdir, mkdir + '\n    find "$ODIN_DIR/${MODEL}_${CSC}" -maxdepth 1 -type f -name "*.zip" -delete')
    path.write_text(text)

def patch_sequential_firmwares(workspace):
    path = workspace / 'scripts/make_rom.sh'
    text = path.read_text()
    start = '    if [ ! -f "$FW_DIR/$SOURCE_FIRMWARE_PATH/.extracted" ] || [ ! -f "$FW_DIR/$TARGET_FIRMWARE_PATH/.extracted" ]; then'
    end = '    LOG_STEP_IN true "Creating work dir"'
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError('Unexpected firmware preparation block')
    begin, finish = text.index(start), text.index(end)
    text = text[:begin] + '    python3 "$SRC_DIR/integration/samloader/stage.py" "$SRC_DIR" || exit 1\n\n' + text[finish:]
    path.write_text(text)
    path = workspace / 'scripts/download_fw.sh'
    text = path.read_text()
    # Match the exact pinned upstream command, preserving Odin MD5 validation after it.
    line = next((line for line in text.splitlines() if 'EVAL "unzip -o' in line), None)
    if line is None or text.count(line) != 1:
        raise ValueError('Unexpected ZIP expansion command')
    text = text.replace(line, '    python3 "$SRC_DIR/integration/samloader/unpack_reclaim.py" "$ZIP_FILE" "$ODIN_DIR/${MODEL}_${CSC}" || exit 1')
    path.write_text(text)


def patch_firmware_lookup(workspace):
    path = workspace / 'scripts/utils/firmware_utils.sh'
    text = path.read_text()
    replacement = '''GET_LATEST_FIRMWARE()
{
    python3 "$SRC_DIR/integration/samloader/metadata.py" get "$OUT_DIR/firmware-lock.json" "$1" "$2"
}'''
    text, count = re.subn(r'GET_LATEST_FIRMWARE\(\)\n\{.*?\n\}', lambda _: replacement, text, flags=re.S)
    if count != 1:
        raise ValueError('Unexpected firmware lookup helper')
    # Both download_fw.sh and extract_fw.sh call this shared legacy parser.
    # Version/identity selection belongs to the firmware lock, not IMEI parsing.
    parser=(ROOT/'integration/samloader/parse_descriptor.sh').read_text().rstrip()
    text,count=re.subn(r'PARSE_FIRMWARE_STRING\(\)\n\{.*?\n\}',lambda _:parser,text,flags=re.S)
    if count!=1:
        raise ValueError('Unexpected shared firmware descriptor parser')
    text=text.replace('# - IMEI/SN that matches the given model is required to download the firmware from FUS',
                      '# - SmartDownload requires no IMEI/SN; the version is taken from firmware-lock.json')
    text=text.replace('# - The supplied string must be in the following format: <MODEL>/<CSC>/<IMEI/SN>',
                      '# - Accepts <MODEL>/<CSC> with an optional ignored legacy/reference token')
    path.write_text(text)


def patch_parallel_builds(workspace):
    """Track bounded workers in make_rom; the legacy recovery ZIP is not used."""
    relative = 'scripts/make_rom.sh'
    path = workspace / relative
    text = path.read_text()
    old = 'wait $(jobs -p) || exit 1'
    if text.count(old) != 1:
        raise ValueError(f'Unexpected parallel build schema: {relative}')
    wait = "BEYOUD_FAILED=0\nfor BEYOUD_PID in \"${BEYOUD_PIDS[@]}\"; do\n    wait \"$BEYOUD_PID\" || BEYOUD_FAILED=1\ndone\n[ \"$BEYOUD_FAILED\" -eq 0 ] || exit 1"
    text = text.replace(old, wait)
    old_hash = 'find "$SRC_DIR/unica" "$SRC_DIR/target/$TARGET_CODENAME" -type f -print0'
    new_hash = 'find "$SRC_DIR/unica" "$SRC_DIR/target/$TARGET_CODENAME" "$SRC_DIR/platform/$TARGET_PLATFORM" "$SRC_DIR/integration" "$OUT_DIR/firmware-lock.json" -type f -print0'
    text = text.replace(old_hash, new_hash)
    start = '        while IFS= read -r f; do'
    end = '        done < <(find "$APKTOOL_DIR"'
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError('Unexpected APK worker loop')
    text = text.replace(start, '        BEYOUD_PIDS=()\n' + start)
    text = text.replace(end, '            BEYOUD_PIDS+=("$!")\n' + end)
    path.write_text(text)


def install_s10_kernel_builder(workspace):
    """Activate the pinned S10 kernel hook without losing OneROM source state."""
    workspace = Path(workspace).resolve(strict=True)
    module = workspace / 'platform/exynos9820/patches/extremekrnl'
    module_prop = module / 'module.prop'
    active_hook = module / 'customize.sh'
    disable_marker = module / 'disable'
    source_root = ROOT / 'integration/onerom/upstream/platform/exynos9820/patches/extremekrnl'
    pinned_customization = source_root / 'customize.sh'
    pinned_disable = source_root / 'disable'
    replacement_hook = ROOT / 'integration/artisan/extremekrnl.sh'
    upstream_reference = workspace / 'reference/onerom-upstream/platform/exynos9820/patches/extremekrnl'
    upstream_customization = upstream_reference / 'customize.sh'
    upstream_disable = upstream_reference / 'disable'

    for directory, description in (
        (module, 'OneROM kernel module'),
        (workspace / 'reference/onerom-upstream', 'OneROM provenance directory'),
    ):
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f'Missing or unsafe {description}: {directory}')
    for path, description in (
        (module_prop, 'OneROM kernel module metadata'),
        (active_hook, 'active OneROM kernel customization'),
        (disable_marker, 'active OneROM kernel disable marker'),
        (pinned_customization, 'pinned OneROM kernel customization'),
        (pinned_disable, 'pinned OneROM kernel disable marker'),
        (replacement_hook, 'pinned Artisan kernel build hook'),
        (upstream_customization, 'preserved OneROM kernel customization'),
    ):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'Missing or unsafe {description}: {path}')
    if (active_hook.read_bytes() != pinned_customization.read_bytes()
            or upstream_customization.read_bytes() != pinned_customization.read_bytes()):
        raise ValueError('Active or preserved OneROM kernel customization differs from its pinned source')
    if disable_marker.read_bytes() != pinned_disable.read_bytes():
        raise ValueError('OneROM kernel disable marker differs from the pinned source')
    if upstream_disable.exists() or upstream_disable.is_symlink():
        if (upstream_disable.is_symlink() or not upstream_disable.is_file()
                or upstream_disable.read_bytes() != pinned_disable.read_bytes()):
            raise ValueError('Preserved OneROM kernel disable marker differs from the pinned source')
    else:
        shutil.copy2(disable_marker, upstream_disable)

    # apply_modules.sh returns immediately when `disable` exists, before it
    # sources customize.sh. The upstream marker stays byte-exact in provenance;
    # only the active project module is enabled so its pinned compiler can emit
    # the required boot.img, dtb.img, and dtbo.img.
    disable_marker.unlink()
    shutil.copyfile(replacement_hook, active_hook)
    return {
        'status': 'pinned-kernel-hook-active',
        'hook': 'integration/artisan/extremekrnl.sh',
        'kernel_repository': 'Android-Artisan/android_kernel_samsung_exynos9820',
        'kernel_revision': '9a0a792d227c8ae6cddac0c9d68a8bb9782c44cb',
        'required_images': ['boot.img', 'dtb.img', 'dtbo.img'],
        'upstream_disable_marker': str(upstream_disable.relative_to(workspace)),
        'upstream_disable_marker_sha256': hashlib.sha256(pinned_disable.read_bytes()).hexdigest(),
        'upstream_kernel_binaries': 'preserved; not substituted for pinned build outputs',
    }


def apply_overlay(workspace, codename=DEFAULT_TARGET):
    device = select(codename)
    donor=json.loads((ROOT/'integration/donors/s24fe.json').read_text())
    raw=(ROOT/'integration/donors/s24fe.sh').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=donor['sha256']:
        raise ValueError('S24 FE donor config differs from pinned provenance')
    model = device["model"]
    # The complete OneROM tree is scoped to the normal S10. Preserve the
    # established S10+ compatibility path rather than inferring a port there.
    onerom_port = import_onerom_sources(workspace, codename)
    shutil.copytree(ROOT / 'integration', workspace / 'integration')
    # The generated package embeds pinned source/license provenance in its ZIP;
    # make the checked manifests available inside this standalone workspace.
    manifest_destination = workspace / 'manifests'
    if manifest_destination.exists() or manifest_destination.is_symlink():
        raise ValueError('Refusing to overwrite existing workspace manifests')
    shutil.copytree(ROOT / 'manifests', manifest_destination)
    shutil.copyfile(ROOT / 'integration/artisan/essi_64.sh',
                    workspace / 'unica/configs/essi_64.sh')
    kernel_module = workspace / 'platform/exynos9820/patches/extremekrnl/customize.sh'
    kernel_module.parent.mkdir(parents=True, exist_ok=True)
    if codename == 'beyond1lte':
        kernel_build = install_s10_kernel_builder(workspace)
    else:
        # Keep the existing S10+ behavior; the complete OneROM source port and
        # this reactivation policy are scoped to the normal SM-G973F only.
        shutil.copyfile(ROOT / 'integration/artisan/extremekrnl.sh', kernel_module)
        kernel_build = None
    patch_downloader(workspace)
    patch_firmware_lookup(workspace)
    patch_parallel_builds(workspace)
    patch_sequential_firmwares(workspace)
    install_framework(workspace)
    install_preflight(workspace)
    install_runtime_paths(workspace)
    apply_build_policy(workspace)
    if codename == 'beyond1lte':
        s10_compatibility = install_s10_compat(workspace, codename)
        onerom = {
            'repository': 'DaDevMikey/OneROM',
            'commit': onerom_port['commit'],
            'active': s10_compatibility['active'],
            'disabled_candidates': onerom_port['upstream_disabled_modules'],
        }
    else:
        s10_compatibility = None
        onerom = install_onerom(workspace, codename)
    target = workspace / 'target' / codename / 'config.sh'
    text = target.read_text()
    expected = f'TARGET_ASSERT_MODEL=("{model}" "{device["legacy_model"]}")'
    if expected not in text or f'TARGET_CODENAME="{codename}"' not in text:
        raise ValueError('Unexpected base device configuration')
    text = text.replace(expected, f'TARGET_ASSERT_MODEL=("{model}")')
    if codename == 'beyond1lte':
        # OneROM names its own donor config r12s_native, but this build keeps
        # Artisan's active S24 FE adapter as unica/configs/essi_64.sh. Select
        # that existing Artisan path rather than a file that is not installed.
        onerom_image = 'TARGET_SINGLE_SYSTEM_IMAGE="r12s_native"'
        if text.count(onerom_image) != 1:
            raise ValueError('Unexpected pinned OneROM S10 single-system-image selection')
        text = text.replace(onerom_image, 'TARGET_SINGLE_SYSTEM_IMAGE="essi"', 1)
    text = text.replace('TARGET_EXTRA_FIRMWARES=("")', 'TARGET_EXTRA_FIRMWARES=()')
    target.write_text(text)
    version = workspace / 'unica/configs/version.sh'
    if version.exists():
        with version.open('a') as stream:
            stream.write('\n# Unofficial test candidate, not an ArtisanROM release.\nROM_VERSION="0.1.0-alpha1"\nROM_CODENAME="Beyoud"\n')
    (workspace / 'BEYOUD-WORKSPACE.json').write_text(json.dumps({
        'base_commit': BASE_COMMIT, 'status': 'unvalidated-candidate',
        'target': model, 'codename': codename, 'flashable_release': False,
        'onerom_compatibility': onerom,
        'onerom_port': onerom_port,
        's10_compatibility': s10_compatibility,
        'kernel_build': kernel_build,
        'donor_commit': donor['commit'],
        'donor_profile': donor,
        'tooling_source_commit': '609fa7cc738e42dedcc31ffecbe4aefc0b34d6e2',
        'note': 'Legacy framework patches retained for compatibility investigation; not migrated.'
    }, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--target', choices=sorted(TARGETS), default=DEFAULT_TARGET)
    parser.add_argument('--archive', type=Path, help='Previously downloaded pinned archive')
    parser.add_argument('--discard-archive', action='store_true', help='Delete only the automatically managed archive after successful assembly')
    args = parser.parse_args()
    if args.discard_archive and args.archive is not None:
        parser.error('--discard-archive cannot delete a user-supplied --archive')
    destination = args.destination.resolve()
    if destination.exists():
        parser.error('Destination must not exist; existing work is never overwritten')
    if destination == ROOT or ROOT in destination.parents:
        parser.error('Use a workspace OUTSIDE the repository')
    archive = args.archive or destination.parent / f'artisan-{BASE_COMMIT}.tar.gz'
    if not archive.exists():
        archive.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['curl', '--fail', '--location', '--retry', '2',
                        f'https://codeload.github.com/{BASE_REPO}/tar.gz/{BASE_COMMIT}',
                        '-o', str(archive)], check=True)
    check_archive(archive)
    destination.mkdir(parents=True)
    extract(archive, destination)
    apply_overlay(destination, args.target)
    if args.discard_archive:
        archive.unlink()
    print(f'Candidate assembled: {destination}')
    print('External submodules are NOT included in the archive. See docs/INTEGRATION.md.')


if __name__ == '__main__':
    main()
