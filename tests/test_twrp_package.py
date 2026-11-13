import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from integration import twrp_package


class TWRPPackageTests(unittest.TestCase):
    MODEL = 'SM-G973F'
    CODENAME = 'beyond1lte'

    def workspace(self, root):
        (root / 'out').mkdir()
        (root / 'BEYOUD-WORKSPACE.json').write_text(json.dumps({
            'target': self.MODEL,
            'codename': self.CODENAME,
            'status': 'unvalidated-candidate',
            'source_commit': 'a' * 40,
        }))
        lock = root / 'out/firmware-lock.json'
        lock.write_text(json.dumps({'schema_version': 1, 'firmwares': []}))
        return lock

    def fixtures(self, root):
        lock = self.workspace(root)
        raw_dir = root / 'out/raw-images' / self.CODENAME
        raw_dir.mkdir(parents=True)
        (raw_dir / 'system.img').write_bytes(b'raw-image')
        raw_proof = root / twrp_package.RAW_PROOF_ROOT / f'{self.CODENAME}.json'
        raw_proof.parent.mkdir(parents=True)
        raw_proof.write_text(json.dumps({'firmware_lock_sha256': hashlib.sha256(lock.read_bytes()).hexdigest()}))
        return lock, raw_dir, raw_proof

    @staticmethod
    def zip_report(package):
        return {
            'status': 'twrp-rom-zip-host-verified',
            'package': package.name,
            'bytes': package.stat().st_size,
            'sha256': twrp_package.sha256(package),
            'target_model': 'SM-G973F',
            'target_codename': 'beyond1lte',
            'images': ['system', 'vendor', 'product', 'dtb', 'dtbo', 'boot'],
            'image_count': 6,
            'recovery_included': False,
            'recovery_modified': False,
            'hardware_validated': False,
        }

    def test_builds_and_revalidates_one_twrp_zip_with_private_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _lock, raw_dir, _raw_proof = self.fixtures(root)
            report = {'images': ['system', 'vendor', 'product', 'dtb', 'dtbo', 'boot']}

            def fake_raw_build(workspace):
                return raw_dir

            def fake_zip_build(images, output, receipt=None):
                output.write_bytes(b'validated-by-mock-zip-builder')
                return [{'name': name} for name in report['images']]

            with patch.dict(os.environ, {
                'BEYOUD_OUTPUT_FORMAT': 'twrp-zip',
                'BEYOUD_ALPHA_VERSION': '3.2',
                'GITHUB_RUN_NUMBER': '42',
                'GITHUB_RUN_ATTEMPT': '2',
            }, clear=True), \
                 patch.object(twrp_package, 'build_raw_images', side_effect=fake_raw_build), \
                 patch.object(twrp_package, 'verify_raw_bundle', return_value=report), \
                 patch.object(twrp_package, 'build_twrp_zip', side_effect=fake_zip_build), \
                 patch.object(twrp_package, 'verify_twrp_zip', side_effect=lambda package, **kwargs: self.zip_report(package)):
                result = twrp_package.build_workspace(root)
                verified = twrp_package.verify_workspace(root)

            self.assertEqual(result['status'], 'twrp-rom-zip-host-verified')
            self.assertEqual(verified['images'], report['images'])
            self.assertFalse(verified['recovery_included'])
            self.assertFalse(verified['hardware_validated'])
            zip_dir = root / twrp_package.OUTPUT_ROOT / self.CODENAME
            self.assertEqual(len(list(zip_dir.glob('*.zip'))), 1)
            proof = json.loads((root / twrp_package.PROOF_ROOT / f'{self.CODENAME}.json').read_text())
            self.assertEqual(proof['signature_status'], 'unsigned-test-package')
            self.assertFalse(proof['recovery_modified'])

    def test_wrong_target_rejected_before_raw_image_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.workspace(root)
            marker = json.loads((root / 'BEYOUD-WORKSPACE.json').read_text())
            marker['target'] = 'SM-G975F'
            marker['codename'] = 'beyond2lte'
            (root / 'BEYOUD-WORKSPACE.json').write_text(json.dumps(marker))
            with patch.object(twrp_package, 'build_raw_images') as build_images:
                with self.assertRaisesRegex(ValueError, 'SM-G973F / beyond1lte only'):
                    twrp_package.build_workspace(root)
                build_images.assert_not_called()


if __name__ == '__main__':
    unittest.main()
