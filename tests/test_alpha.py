import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('alpha', ROOT / 'scripts/collect_alpha.py')
alpha = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alpha)


def package(path, model='SM-G975F', boot=b'candidate-boot', payload=True):
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('META-INF/com/google/android/update-binary', b'installer')
        archive.writestr('META-INF/com/google/android/updater-script', f'getprop("ro.product.model") == "{model}"')
        archive.writestr('boot.img', boot)
        archive.writestr('dtbo.img', b'candidate-dtbo')
        if payload:
            archive.writestr('system.new.dat.br', b'candidate-system')


class AlphaTests(unittest.TestCase):
    def test_wrong_model_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'rom.zip'
            package(path, model='SM-G985F')
            with self.assertRaises(ValueError):
                alpha.check_package(path)

    def test_empty_boot_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'rom.zip'
            package(path, boot=b'')
            with self.assertRaises(ValueError):
                alpha.check_package(path)

    def test_missing_system_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'rom.zip'
            package(path, payload=False)
            with self.assertRaises(ValueError):
                alpha.check_package(path)

    def test_no_zip_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / 'work'
            workspace.mkdir()
            (workspace / 'BEYOUD-WORKSPACE.json').write_text(json.dumps({'target': 'SM-G975F'}))
            dest = Path(tmp) / 'output'
            with self.assertRaises(ValueError):
                alpha.collect(workspace, dest)
            self.assertFalse(dest.exists())

    def test_structural_checks_are_not_hardware_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / 'work'
            (workspace / 'out').mkdir(parents=True)
            (workspace / 'BEYOUD-WORKSPACE.json').write_text(json.dumps({'target': 'SM-G975F', 'flashable_release': False}))
            package(workspace / 'out/ArtisanROM_0.1.0-alpha1_beyond2lte.zip')
            dest = Path(tmp) / 'output'
            with patch.object(alpha, 'load_package_inputs', return_value={'stock_image_size_caps': {'system': 1000}}):
                alpha.collect(workspace, dest)
            self.assertTrue((dest / 'SHA256SUMS').exists())
            self.assertIn('DO NOT prove boot', (dest / 'WARNING.txt').read_text())

    def test_public_build_identity_is_numbered_and_zip_bytes_are_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / 'work'
            (workspace / 'out').mkdir(parents=True)
            (workspace / 'BEYOUD-WORKSPACE.json').write_text(json.dumps({
                'target': 'SM-G973F', 'codename': 'beyond1lte', 'flashable_release': False,
            }))
            source = workspace / 'out/ArtisanROM_0.1.0-alpha1_beyond1lte.zip'
            package(source, model='SM-G973F')
            original_zip = source.read_bytes()
            destination = Path(tmp) / 'numbered-alpha'
            package_inputs = {
                'stock_image_size_caps': {'system': 1000},
                'partition_layout': {'id': 'stock'},
            }
            with patch.object(alpha, 'load_package_inputs', return_value=package_inputs):
                alpha.collect(workspace, destination, alpha_version='3.1', build_number=23, run_attempt=2)

            filename = 'X-NovaOS-SM-G973F-Alpha-3.1-Build-23-Attempt-2-UNTESTED.zip'
            output = destination / filename
            self.assertTrue(output.is_file())
            self.assertEqual(output.read_bytes(), original_zip)
            self.assertIn('X-NovaOS Alpha 3.1 — build #23, attempt 2', (destination / 'WARNING.txt').read_text())
            info = json.loads((destination / 'BUILD-INFO.json').read_text())
            self.assertEqual(info['project'], 'X-NovaOS')
            self.assertEqual(info['version'], 'Alpha 3.1')
            self.assertEqual(info['build_number'], 23)
            self.assertEqual(info['run_attempt'], 2)
            self.assertEqual(info['target_model'], 'SM-G973F')
            self.assertFalse(info['release_published'])
            self.assertFalse(info['hardware_validated'])
            self.assertFalse(info['zip_bytes_modified'])
            self.assertEqual(info['sha256'], hashlib.sha256(original_zip).hexdigest())
            self.assertIn(filename, (destination / 'SHA256SUMS').read_text())

    def test_invalid_public_build_identity_is_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / 'should-not-exist'
            with self.assertRaises(ValueError):
                alpha.collect(Path(tmp) / 'not-read', destination, alpha_version='../3', build_number=1)
            with self.assertRaises(ValueError):
                alpha.collect(Path(tmp) / 'not-read', destination, alpha_version='3.1')
            with self.assertRaises(ValueError):
                alpha.collect(Path(tmp) / 'not-read', destination, alpha_version='3.1', build_number=1, run_attempt=0)
            self.assertFalse(destination.exists())

    def test_unsupported_partition_payload_or_write_is_rejected(self):
        for mode in ('payload','script','boot'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'rom.zip';package(path)
                with zipfile.ZipFile(path,'a') as archive:
                    if mode=='payload':archive.writestr('optics.new.dat.br',b'wrong-target')
                    elif mode=='boot':archive.writestr('init_boot.img',b'wrong-target')
                if mode=='script':
                    other=Path(tmp)/'rewritten.zip'
                    with zipfile.ZipFile(path) as source,zipfile.ZipFile(other,'w') as target:
                        for name in source.namelist():
                            data=source.read(name)
                            if name.endswith('updater-script'):
                                data+=b'\nblock_image_update("/dev/block/by-name/prism", "payload");'
                            target.writestr(name,data)
                    path=other
                with self.assertRaises(ValueError):alpha.check_package(path,allowed_partitions={'system','vendor','product'})

    def test_wrapper_propagates_build_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / 'BEYOUD-WORKSPACE.json').write_text('{"target":"SM-G975F"}')
            (workspace / 'buildenv.sh').write_text('return 0\n')
            (workspace / 'integration').mkdir()
            (workspace / 'integration/build.py').write_text('import sys; print("failed-build"); sys.exit(7)\n')
            scripts = workspace / 'scripts'
            scripts.mkdir()
            make = scripts / 'make_rom.sh'
            make.write_text('#!/bin/bash\necho failed-build\nexit 7\n')
            make.chmod(0o755)
            result = subprocess.run(['bash', str(ROOT / 'scripts/build_candidate.sh'), str(workspace), 'alpha'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 7)
            self.assertTrue(list((workspace / 'out/beyoud-logs').glob('alpha-*.log')))


if __name__ == '__main__':
    unittest.main()
