import contextlib
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from integration import raw_images


class RawImageTests(unittest.TestCase):
    MODEL = 'SM-G973F'
    CODENAME = 'beyond1lte'
    PARTITIONS = ('system', 'vendor', 'product', 'odm', 'prism', 'optics', 'vendor_dlkm')

    @staticmethod
    def ext4_image():
        image = bytearray(4096)
        image[1024 + 0x38:1024 + 0x3A] = b'\x53\xef'
        return bytes(image)

    def workspace(self, root, *, optional=True):
        (root / 'out').mkdir()
        (root / 'BEYOUD-WORKSPACE.json').write_text(json.dumps({
            'target': self.MODEL, 'codename': self.CODENAME,
            'status': 'unvalidated-candidate',
        }))
        (root / 'out/firmware-lock.json').write_text(json.dumps({
            'schema_version': 1, 'firmwares': [{'model': self.MODEL, 'csc': 'AUT'}],
        }))
        target = root / 'target' / self.CODENAME
        target.mkdir(parents=True)
        (target / 'config.sh').write_text(
            'TARGET_CODENAME="beyond1lte"\n'
            'TARGET_ASSERT_MODEL=("SM-G973F")\n'
            'TARGET_OS_FILE_SYSTEM="ext4"\n'
            'TARGET_SUPER_PARTITION_SIZE=0\n'
            'TARGET_HAS_SYSTEM_EXT=false\n'
        )
        (root / 'scripts').mkdir()
        (root / 'scripts/build_fs_image.sh').write_text('#!/bin/sh\n')
        work = root / 'out/target' / self.CODENAME / 'work_dir'
        kernel = work / 'kernel'
        configs = work / 'configs'
        kernel.mkdir(parents=True)
        configs.mkdir()
        partitions = list(self.PARTITIONS if optional else ('system', 'vendor', 'product'))
        for name in partitions:
            tree = work / name
            tree.mkdir()
            (tree / 'example-file').write_text(f'{name} payload')
            (configs / f'file_context-{name}').write_text(f'/{name} u:object_r:system_file:s0\n')
            (configs / f'fs_config-{name}').write_text(f'{name} 0 0 755\n')
        (kernel / 'boot.img').write_bytes(b'ANDROID!' + bytes(256))
        (kernel / 'dtb.img').write_bytes(bytes.fromhex('d00dfeed') + bytes(128))
        (kernel / 'dtbo.img').write_bytes(bytes.fromhex('d7b7ab1e') + bytes(128))
        (work / 'up_param.bin').write_bytes(b'not-an-img')
        caps = {name: 64 * 1024 for name in raw_images.FILESYSTEM_ORDER}
        inputs = {
            'schema_version': 1,
            'codename': self.CODENAME,
            'model': self.MODEL,
            'partition_layout': {'id': 'stock'},
            'stock_image_size_caps': caps,
        }
        environment = {
            'BEYOUD_OUTPUT_FORMAT': 'twrp-zip',
            'BEYOUD_ALPHA_VERSION': '3.2',
            'BEYOUD_JOBS': '1',
            'TARGET_CODENAME': self.CODENAME,
            'TARGET_ASSERT_MODEL': self.MODEL,
            'TARGET_OS_FILE_SYSTEM': 'ext4',
            'WORK_DIR': str(work.resolve()),
            'GITHUB_RUN_NUMBER': '42',
            'GITHUB_RUN_ATTEMPT': '2',
            'GITHUB_RUN_ID': '123456',
            'GITHUB_REPOSITORY': 'owner/X-NovaOS',
            'GITHUB_SHA': 'a' * 40,
        }
        return work, inputs, environment

    def image_builder(self, *, sparse_system=False):
        def run(command, **kwargs):
            if Path(command[0]).name == 'build_fs_image.sh':
                output = Path(command[command.index('-o') + 1])
                if sparse_system and output.name == '.build-system.img':
                    output.write_bytes(struct.pack('<I', raw_images.SPARSE_MAGIC) + bytes(24))
                else:
                    output.write_bytes(self.ext4_image())
            elif command[0] == 'simg2img':
                Path(command[2]).write_bytes(self.ext4_image())
            else:
                raise AssertionError(f'Unexpected host tool invocation: {command}')
            return MagicMock(returncode=0)
        return run

    def build_patches(self, inputs, environment, *, sparse_system=False):
        return (
            patch.dict(os.environ, environment, clear=True),
            patch.object(raw_images, 'load_package_inputs', return_value=inputs),
            patch.object(raw_images.subprocess, 'run', side_effect=self.image_builder(sparse_system=sparse_system)),
            patch.object(raw_images, 'verify_image', side_effect=lambda path: {
                'status': 'filesystem-verified',
                'filesystem': raw_images._detect_filesystem(path),
                'sparse': False,
            }),
        )

    def test_raw_bundle_rejects_unreviewed_s10_plus_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.workspace(root)
            (root / 'BEYOUD-WORKSPACE.json').write_text(json.dumps({
                'target': 'SM-G975F', 'codename': 'beyond2lte',
                'status': 'unvalidated-candidate',
            }))
            with self.assertRaisesRegex(ValueError, 'only SM-G973F / beyond1lte'):
                raw_images.build(root)

    def test_build_publishes_only_imgs_and_collects_all_existing_supported_partitions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, inputs, environment = self.workspace(root)
            with contextlib.ExitStack() as stack:
                for item in self.build_patches(inputs, environment):
                    stack.enter_context(item)
                with contextlib.redirect_stdout(io.StringIO()):
                    result = raw_images.build(root)
            expected = set(self.PARTITIONS) | {'boot', 'dtb', 'dtbo'}
            self.assertEqual({path.stem for path in result.iterdir()}, expected)
            self.assertTrue(all(path.is_file() and path.suffix == '.img' for path in result.iterdir()))
            self.assertFalse(list(result.glob('*.*json')))
            self.assertFalse(list(result.glob('*.txt')))
            proof_path = root / raw_images.PROOF_ROOT / f'{self.CODENAME}.json'
            proof = json.loads(proof_path.read_text())
            self.assertEqual({record['name'] for record in proof['images']}, expected)
            self.assertEqual(proof['required_images'], ['system', 'vendor', 'product', 'dtb', 'dtbo', 'boot'])
            self.assertIn('up_param.bin', proof['build']['excluded_non_image_components'])
            validation = raw_images.verify_bundle(
                result, self.MODEL, self.CODENAME, receipt=proof_path, verify_hashes=True,
            )
            self.assertEqual(validation['status'], 'raw-images-verified')
            self.assertFalse(validation['hardware_validated'])

    def test_sparse_filesystem_intermediate_is_expanded_before_delivery(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, inputs, environment = self.workspace(root, optional=False)
            with contextlib.ExitStack() as stack:
                for item in self.build_patches(inputs, environment, sparse_system=True):
                    stack.enter_context(item)
                with contextlib.redirect_stdout(io.StringIO()):
                    result = raw_images.build(root)
            image = result / 'system.img'
            self.assertNotEqual(image.read_bytes()[:4], struct.pack('<I', raw_images.SPARSE_MAGIC))
            receipt = root / raw_images.PROOF_ROOT / f'{self.CODENAME}.json'
            raw_images.verify_bundle(result, self.MODEL, self.CODENAME, receipt=receipt)

    def test_optional_init_boot_and_vendor_boot_are_included_when_present(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work, inputs, environment = self.workspace(root, optional=False)
            (work / 'kernel/init_boot.img').write_bytes(b'ANDROID!' + bytes(64))
            (work / 'kernel/vendor_boot.img').write_bytes(b'ANDROID!' + bytes(64))
            with contextlib.ExitStack() as stack:
                for item in self.build_patches(inputs, environment):
                    stack.enter_context(item)
                with contextlib.redirect_stdout(io.StringIO()):
                    result = raw_images.build(root)
            self.assertTrue((result / 'init_boot.img').is_file())
            self.assertTrue((result / 'vendor_boot.img').is_file())
            receipt = root / raw_images.PROOF_ROOT / f'{self.CODENAME}.json'
            report = raw_images.verify_bundle(result, self.MODEL, self.CODENAME, receipt=receipt)
            self.assertIn('init_boot', report['images'])
            self.assertIn('vendor_boot', report['images'])

    def test_boot_dtb_dtbo_are_all_required_for_pinned_s10_kernel(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work, inputs, environment = self.workspace(root, optional=False)
            (work / 'kernel/dtb.img').unlink()
            with contextlib.ExitStack() as stack:
                for item in self.build_patches(inputs, environment):
                    stack.enter_context(item)
                with self.assertRaisesRegex(ValueError, 'dtb'):
                    raw_images.build(root)
            self.assertFalse((root / 'out/raw-images' / self.CODENAME).exists())

    def test_separate_system_ext_is_rejected_when_target_config_embeds_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work, inputs, environment = self.workspace(root, optional=False)
            tree = work / 'system_ext'
            tree.mkdir()
            (tree / 'payload').write_text('unexpected separate system_ext')
            (work / 'configs/file_context-system_ext').write_text('/system_ext u:object_r:system_file:s0\n')
            (work / 'configs/fs_config-system_ext').write_text('system_ext 0 0 755\n')
            inputs['stock_image_size_caps']['system_ext'] = 64 * 1024
            with contextlib.ExitStack() as stack:
                for item in self.build_patches(inputs, environment):
                    stack.enter_context(item)
                with self.assertRaisesRegex(ValueError, 'embeds system_ext'):
                    raw_images.build(root)

    def test_partition_image_over_capacity_fails_without_publishing_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, inputs, environment = self.workspace(root, optional=False)
            inputs['stock_image_size_caps']['system'] = 1024
            with contextlib.ExitStack() as stack:
                for item in self.build_patches(inputs, environment):
                    stack.enter_context(item)
                with self.assertRaisesRegex(ValueError, 'exceeds physical image capacity'):
                    raw_images.build(root)
            self.assertFalse((root / 'out/raw-images' / self.CODENAME).exists())
            self.assertFalse((root / raw_images.PROOF_ROOT / f'{self.CODENAME}.json').exists())

    def test_receipt_verifier_rejects_non_img_files_hash_changes_and_wrong_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, inputs, environment = self.workspace(root, optional=False)
            with contextlib.ExitStack() as stack:
                for item in self.build_patches(inputs, environment):
                    stack.enter_context(item)
                with contextlib.redirect_stdout(io.StringIO()):
                    bundle = raw_images.build(root)
            proof = root / raw_images.PROOF_ROOT / f'{self.CODENAME}.json'
            receipt = json.loads(proof.read_text())
            with self.assertRaisesRegex(ValueError, 'model mismatch'):
                raw_images.verify_bundle(bundle, 'SM-G975F', self.CODENAME, receipt=receipt)
            (bundle / 'WARNING.txt').write_text('not allowed in the image-only deliverable')
            with self.assertRaisesRegex(ValueError, r'\.img files only'):
                raw_images.verify_bundle(bundle, self.MODEL, self.CODENAME, receipt=receipt)
            (bundle / 'WARNING.txt').unlink()
            with (bundle / 'system.img').open('ab') as stream:
                stream.write(b'tamper')
            with self.assertRaisesRegex(ValueError, 'size mismatch|SHA-256 mismatch'):
                raw_images.verify_bundle(bundle, self.MODEL, self.CODENAME, receipt=receipt)

    def test_target_config_and_environment_must_prove_exact_static_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, _, environment = self.workspace(root, optional=False)
            config = root / 'target' / self.CODENAME / 'config.sh'
            self.assertEqual(raw_images._validate_target_config(
                config, self.MODEL, self.CODENAME, environment,
            )['super_partition_size'], 0)
            config.write_text(config.read_text().replace('TARGET_ASSERT_MODEL=("SM-G973F")',
                                                         'TARGET_ASSERT_MODEL=("SM-G973F" "SM-G973N")'))
            with self.assertRaisesRegex(ValueError, 'static S10 partition layout'):
                raw_images._validate_target_config(config, self.MODEL, self.CODENAME, environment)


if __name__ == '__main__':
    unittest.main()
