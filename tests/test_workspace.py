import importlib.util
import io
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare', ROOT / 'scripts/prepare_workspace.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class WorkspaceTests(unittest.TestCase):
    def test_s10_kernel_hook_activates_module_and_preserves_upstream_disable_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            module = workspace / 'platform/exynos9820/patches/extremekrnl'
            provenance = workspace / 'reference/onerom-upstream/platform/exynos9820/patches/extremekrnl'
            module.mkdir(parents=True)
            provenance.mkdir(parents=True)
            source = ROOT / 'reference/onerom-port-candidates/source-snapshot/platform/exynos9820/patches/extremekrnl'
            original_customization = (source / 'customize.sh').read_bytes()
            original_disable = (source / 'disable').read_bytes()
            (module / 'module.prop').write_text('id=extremekrnl\n')
            (module / 'customize.sh').write_bytes(original_customization)
            (module / 'disable').write_bytes(original_disable)
            (provenance / 'customize.sh').write_bytes(original_customization)

            record = prepare.install_s10_kernel_builder(workspace)

            self.assertEqual(record['status'], 'pinned-kernel-hook-active')
            self.assertFalse((module / 'disable').exists())
            self.assertEqual((provenance / 'disable').read_bytes(), original_disable)
            self.assertEqual((provenance / 'customize.sh').read_bytes(), original_customization)
            self.assertEqual((module / 'customize.sh').read_bytes(),
                             (ROOT / 'integration/artisan/extremekrnl.sh').read_bytes())
            self.assertEqual(record['upstream_disable_marker_sha256'],
                             'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
            self.assertEqual(record['required_images'], ['boot.img', 'dtb.img', 'dtbo.img'])

            # Match the module loader's disable guard and sourcing order, while
            # the pinned hook's preflight path prevents a compiler invocation.
            script = '''\nMODPATH="$1"\nif [ ! -f "$MODPATH/module.prop" ]; then exit 2; elif [ -f "$MODPATH/disable" ]; then echo disabled; exit 0; fi\nBEYOUD_PATCH_PREFLIGHT=1\nTARGET_CODENAME=beyond1lte\n. "$MODPATH/customize.sh"\necho hook-loaded\n'''
            executed = subprocess.run(['bash', '-c', script, 'test', str(module)],
                                      check=True, capture_output=True, text=True)
            self.assertIn('Patch preflight: deferring pinned kernel compilation', executed.stdout)
            self.assertIn('hook-loaded', executed.stdout)
            self.assertNotIn('disabled', executed.stdout)

    def test_s10_kernel_builder_rejects_changed_disable_marker_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            module = workspace / 'platform/exynos9820/patches/extremekrnl'
            provenance = workspace / 'reference/onerom-upstream/platform/exynos9820/patches/extremekrnl'
            module.mkdir(parents=True)
            provenance.mkdir(parents=True)
            source = ROOT / 'reference/onerom-port-candidates/source-snapshot/platform/exynos9820/patches/extremekrnl'
            original_customization = (source / 'customize.sh').read_bytes()
            (module / 'module.prop').write_text('id=extremekrnl\n')
            (module / 'customize.sh').write_bytes(original_customization)
            (module / 'disable').write_bytes(b'unexpected\n')
            (provenance / 'customize.sh').write_bytes(original_customization)

            with self.assertRaisesRegex(ValueError, 'disable marker differs'):
                prepare.install_s10_kernel_builder(workspace)
            self.assertTrue((module / 'disable').is_file())
            self.assertEqual((module / 'customize.sh').read_bytes(), original_customization)
            self.assertFalse((provenance / 'disable').exists())

    def test_adapter_preserves_separate_target(self):
        result = subprocess.run(['bash', '-c',
            'SRC_DIR="$1"; source "$1/integration/artisan/essi_64.sh"; '
            'printf "%s|%s|%s" "$SOURCE_API_LEVEL" "$SOURCE_FIRMWARE" "${TARGET_PLATFORM-unset}"',
            'test', str(ROOT)], check=True, capture_output=True, text=True)
        self.assertEqual(result.stdout, '37|SM-S721B/EUX/S721BXXSFEZJ1|unset')

    def test_overlay_only_changes_assertions_and_empty_extra(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            target = workspace / 'target/beyond2lte/config.sh'
            target.parent.mkdir(parents=True)
            original = 'TARGET_CODENAME="beyond2lte"\nTARGET_ASSERT_MODEL=("SM-G975F" "SM-G975N")\nTARGET_EXTRA_FIRMWARES=("")\nTARGET_OS_FILE_SYSTEM="ext4"\nTARGET_SUPER_PARTITION_SIZE=0\n'
            target.write_text(original)
            (workspace / 'unica/configs').mkdir(parents=True)
            (workspace / 'unica/configs/version.sh').write_text('ROM_VERSION="3.1.1"\n')
            from test_smart_download import LEGACY
            (workspace / 'scripts').mkdir()
            (workspace / 'scripts/download_fw.sh').write_text(LEGACY)
            misc = workspace / 'platform/exynos9820/patches/miscs/customize.sh'
            misc.parent.mkdir(parents=True, exist_ok=True)
            misc.write_text((ROOT / 'reference/artisan-s10/platform/exynos9820/patches/miscs/customize.sh').read_text())
            with patch.object(prepare, 'install_runtime_paths'), patch.object(prepare, 'install_preflight'), patch.object(prepare, 'install_framework'), patch.object(prepare, 'apply_build_policy'), patch.object(prepare, 'patch_firmware_lookup'), patch.object(prepare, 'patch_parallel_builds'), patch.object(prepare, 'patch_sequential_firmwares'), patch.object(prepare, 'install_onerom', return_value={'repository': 'test', 'commit': 'test', 'upstream_disabled_modules': []}):
                prepare.apply_overlay(workspace, 'beyond2lte')
            import json
            marker=json.loads((workspace/'BEYOUD-WORKSPACE.json').read_text())
            self.assertEqual(marker['donor_profile']['model'],'SM-S721B')
            self.assertEqual(marker['donor_profile']['reference_version'], 'S721BXXSFEZJ1/S721BOXMFEZJ1/S721BXXSFEZJ1/S721BXXSFEZJ1')
            self.assertEqual(marker['donor_commit'],'541074191937f2d7c033be7a10cf5d99146cc98f')
            self.assertTrue((workspace / 'manifests/onerom.json').is_file())
            self.assertTrue((workspace / 'integration/twrp_zip_builder.py').is_file())
            self.assertIn('0.1.0-alpha1', (workspace / 'unica/configs/version.sh').read_text())
            self.assertIn('TARGET_ASSERT_MODEL=("SM-G975F")', target.read_text())
            self.assertIn('TARGET_SUPER_PARTITION_SIZE=0', target.read_text())
            self.assertIn('TARGET_OS_FILE_SYSTEM="ext4"', target.read_text())

    def test_bad_digest_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.tar.gz'
            path.write_bytes(b'not an archive')
            with self.assertRaises(ValueError):
                prepare.check_archive(path)

    def test_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'bad.tar.gz'
            with tarfile.open(path, 'w:gz') as archive:
                member = tarfile.TarInfo(f'ArtisanROM_old-{prepare.BASE_COMMIT}/../escape')
                member.size = 1
                archive.addfile(member, io.BytesIO(b'x'))
            dest = root / 'dest'
            dest.mkdir()
            with self.assertRaises(ValueError):
                prepare.extract(path, dest)
            self.assertFalse((root / 'escape').exists())

    def test_symlink_cannot_redirect_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'bad.tar.gz'
            with tarfile.open(path, 'w:gz') as archive:
                prefix = f'ArtisanROM_old-{prepare.BASE_COMMIT}/'
                member = tarfile.TarInfo(prefix + 'link')
                member.type = tarfile.SYMTYPE
                member.linkname = str(root)
                archive.addfile(member)
                file = tarfile.TarInfo(prefix + 'link/escape')
                file.size = 1
                archive.addfile(file, io.BytesIO(b'x'))
            dest = root / 'dest'
            dest.mkdir()
            with self.assertRaises(ValueError):
                prepare.extract(path, dest)
            self.assertFalse((root / 'escape').exists())
