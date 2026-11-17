import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from integration import twrp_package
from integration.package_inputs import _layout_image_caps, selected_layout as get_selected_layout


class TWRPPackageTests(unittest.TestCase):
    MODEL = 'SM-G973F'
    CODENAME = 'beyond1lte'

    def workspace(self, root, *, model=None, codename=None):
        model = model or self.MODEL
        codename = codename or self.CODENAME
        (root / 'out').mkdir()
        (root / 'BEYOUD-WORKSPACE.json').write_text(json.dumps({
            'target': model,
            'codename': codename,
            'status': 'unvalidated-candidate',
            'source_commit': 'a' * 40,
        }))
        lock = root / 'out/firmware-lock.json'
        lock.write_text(json.dumps({'schema_version': 1, 'firmwares': []}))
        return lock

    def fixtures(self, root, *, model=None, codename=None, partition_layout='stock'):
        codename = codename or self.CODENAME
        lock = self.workspace(root, model=model, codename=codename)
        stock_caps = {'system': 100000, 'vendor': 100000, 'product': 100000}
        with patch.dict(os.environ, {'BEYOUD_PARTITION_LAYOUT': partition_layout}):
            selected = get_selected_layout(root)
        caps = _layout_image_caps(selected, stock_caps)
        inputs = {
            'schema_version': 1,
            'codename': codename,
            'model': model or self.MODEL,
            'partition_layout': selected,
            'image_size_caps': caps,
            'stock_image_size_caps': stock_caps,
            'firmware_lock_sha256': hashlib.sha256(lock.read_bytes()).hexdigest(),
            'identifiers': {},
        }
        (root / 'out/beyoud-package-inputs.json').write_text(json.dumps(inputs))
        profile_caps = selected.get('image_size_caps', {}) if partition_layout == 'extreme-default' else {}
        profile_structure = selected.get('image_partitions', []) if partition_layout == 'extreme-structure' else []
        raw_dir = root / 'out/raw-images' / codename
        raw_dir.mkdir(parents=True)
        (raw_dir / 'system.img').write_bytes(b'raw-image')
        raw_proof = root / twrp_package.RAW_PROOF_ROOT / f'{codename}.json'
        raw_proof.parent.mkdir(parents=True)
        raw_proof.write_text(json.dumps({
            'firmware_lock_sha256': hashlib.sha256(lock.read_bytes()).hexdigest(),
            'partition_layout': partition_layout,
            'partition_structure': profile_structure,
            'partition_profile_caps': profile_caps,
        }))
        return lock, raw_dir, raw_proof

    @staticmethod
    def zip_report(package, model='SM-G973F', codename='beyond1lte'):
        return {
            'status': 'twrp-rom-zip-host-verified',
            'package': package.name,
            'bytes': package.stat().st_size,
            'sha256': twrp_package.sha256(package),
            'target_model': model,
            'target_codename': codename,
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

            def fake_zip_build(images, output, receipt=None, **kwargs):
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
                 patch.object(twrp_package, 'verify_twrp_zip', side_effect=lambda package, **kwargs: self.zip_report(package, kwargs['expected_model'], kwargs['expected_codename'])):
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

    def test_s10plus_g975f_target_is_exact_and_uses_its_own_package_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.workspace(root, model='SM-G975F', codename='beyond2lte')
            with patch.dict(os.environ, {'BEYOUD_OUTPUT_FORMAT': 'twrp-zip'}, clear=True):
                marker, codename, model = twrp_package._workspace_identity(root)
                paths = twrp_package._output_paths(root, codename, model, 'extreme-structure')
            self.assertEqual((codename, model), ('beyond2lte', 'SM-G975F'))
            self.assertIn('SM-G975F', paths[1].name)
            self.assertIn('EXTREME-STRUCTURE-NO-FIXED-SIZE-CAP', paths[1].name)
            self.assertEqual(paths[1].parent.name, 'beyond2lte')

    def test_s10plus_extreme_structure_candidate_builds_target_locked_zip_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _lock, raw_dir, _raw_proof = self.fixtures(
                root, model='SM-G975F', codename='beyond2lte',
                partition_layout='extreme-structure',
            )
            report = {'images': ['system', 'vendor', 'product', 'dtb', 'dtbo', 'boot']}

            def fake_zip_build(images, output, receipt=None, **kwargs):
                self.assertEqual(kwargs, {'expected_model': 'SM-G975F', 'expected_codename': 'beyond2lte'})
                output.write_bytes(b'validated-by-mock-s10plus-zip-builder')
                return [{'name': name} for name in report['images']]

            with patch.dict(os.environ, {
                'BEYOUD_OUTPUT_FORMAT': 'twrp-zip',
                'BEYOUD_PARTITION_LAYOUT': 'extreme-structure',
                'BEYOUD_ALPHA_VERSION': '3.2',
                'GITHUB_RUN_NUMBER': '52',
                'GITHUB_RUN_ATTEMPT': '1',
            }, clear=True), \
                 patch.object(twrp_package, 'build_raw_images', return_value=raw_dir), \
                 patch.object(twrp_package, 'verify_raw_bundle', return_value=report), \
                 patch.object(twrp_package, 'build_twrp_zip', side_effect=fake_zip_build), \
                 patch.object(twrp_package, 'verify_twrp_zip', side_effect=lambda package, **kwargs: self.zip_report(package, kwargs['expected_model'], kwargs['expected_codename'])):
                result = twrp_package.build_workspace(root)

            self.assertEqual(result['target_model'], 'SM-G975F')
            self.assertEqual(result['target_codename'], 'beyond2lte')
            self.assertEqual(result['partition_layout'], 'extreme-structure')
            self.assertEqual(result['partition_structure'], ['system', 'vendor', 'product', 'odm', 'prism', 'optics'])
            self.assertFalse(result['hardware_validated'])
            package = Path(result['package'])
            self.assertIn('SM-G975F', package.name)
            self.assertIn('EXTREME-STRUCTURE-NO-FIXED-SIZE-CAP', package.name)
            proof = json.loads((root / twrp_package.PROOF_ROOT / 'beyond2lte.json').read_text())
            self.assertEqual(proof['target_model'], 'SM-G975F')
            self.assertEqual(proof['partition_layout'], 'extreme-structure')
            self.assertEqual(proof['partition_structure'], ['system', 'vendor', 'product', 'odm', 'prism', 'optics'])
            self.assertFalse(proof['recovery_included'])
            self.assertFalse(proof['recovery_modified'])
            self.assertFalse(proof['hardware_validated'])

    def test_snapdragon_or_mismatched_target_rejected_before_raw_image_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.workspace(root, model='SM-G975F', codename='beyond1lte')
            with patch.dict(os.environ, {'BEYOUD_OUTPUT_FORMAT': 'twrp-zip'}), \
                 patch.object(twrp_package, 'build_raw_images') as build_images:
                with self.assertRaisesRegex(ValueError, 'mismatch'):
                    twrp_package.build_workspace(root)
                build_images.assert_not_called()


if __name__ == '__main__':
    unittest.main()
