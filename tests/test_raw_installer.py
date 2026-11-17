"""Real ZIP/hash/file-IO tests; NO device node, recovery or actual image flashed."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from integration import twrp_zip_builder as builder

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'integration/new_installer/engine.sh'


class RawInstallerTests(unittest.TestCase):
    def test_bare_fdt_is_not_a_kernel_dt_table_image(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dtb = root / 'dtb.img'
            dtb.write_bytes(bytes.fromhex('d00dfeed') + bytes(128))
            with self.assertRaisesRegex(ValueError, 'Invalid Android DTB table image'):
                builder._validate_image('dtb', dtb, root)

    def fixtures(self, root):
        images = root / 'images'
        images.mkdir()
        for name in builder.REQUIRED:
            if name in {'boot', 'init_boot', 'vendor_boot'}:
                header = b'ANDROID!'
            elif name in {'dtb', 'dtbo'}:
                header = builder.DT_TABLE_MAGIC
            else:
                header = b'fixture-not-real-filesystem'
            (images / (name + '.img')).write_bytes(header + bytes(64))
        package = root / 'candidate.zip'
        # Fixtures are not real filesystems; only filesystem checker is mocked.
        with patch.object(builder, 'verify_image') as verify:
            records = builder.build(images, package)
        self.assertEqual(verify.call_count, 3)
        stage = root / 'stage'
        stage.mkdir()
        with zipfile.ZipFile(package) as archive:
            (stage / 'manifest.tsv').write_bytes(archive.read('installer/manifest.tsv'))
        return images, package, records, stage

    def shell(self, root, package, stage, commands):
        script = '''set -euo pipefail
. "$1"
manifest="$2/manifest.tsv"; stage="$2"; zip="$3"; log="$2/log"
device_base="$4/targets"
ui() { printf '%s\\n' "$*" >> "$log"; }
set_progress() { printf 'progress %s\\n' "$*" >> "$log"; }
''' + commands
        return subprocess.run(['bash', '-c', script, 'test', str(ENGINE), str(stage), str(package), str(root)], text=True, capture_output=True)

    def test_zip_manifest_requires_positive_canonical_decimal_sizes(self):
        names = [name for name in builder.ORDER if name in builder.REQUIRED]
        self.assertEqual(names[-1], 'boot')
        for invalid_size in ('0', '00', '01', '+1', '-1', '1.0'):
            with self.subTest(size=invalid_size):
                content = ''.join(f'{name}{chr(9)}{invalid_size}{chr(9)}{"0" * 64}{chr(10)}' for name in names)
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, 'w') as archive:
                    archive.writestr('installer/manifest.tsv', content)
                buffer.seek(0)
                with zipfile.ZipFile(buffer) as archive:
                    with self.assertRaises(ValueError):
                        builder._read_manifest(archive)

    def test_package_and_all_payload_staging_use_real_zip_and_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images, package, records, stage = self.fixtures(root)
            result = self.shell(root, package, stage, 'validate_manifest\ncheck_staging_space\nstage_images\n')
            self.assertEqual(result.returncode, 0, result.stderr)
            for record in records:
                self.assertEqual((stage / (record['name'] + '.img')).read_bytes(), (images / (record['name'] + '.img')).read_bytes())
            with zipfile.ZipFile(package) as archive:
                entry = archive.read('META-INF/com/google/android/update-binary')
                self.assertNotIn(b'block_image_update', entry)
                self.assertNotIn(b'run_program', entry)
                self.assertIn('images/dtb.img', archive.namelist())
                self.assertNotIn('images/recovery.img', archive.namelist())
                update = archive.getinfo('META-INF/com/google/android/update-binary')
                self.assertTrue((update.external_attr >> 16) & 0o111)
                self.assertEqual(archive.read('installer/zip64-probe.txt'), b'XNOVA_RAW_V1\n')
                self.assertIn(b'GNU GENERAL PUBLIC LICENSE', archive.read(builder.LICENSE_ENTRY))
                notices = archive.read('NOTICES.txt').decode()
                self.assertIn('ArtisanROM', notices)
                self.assertIn('OneROM', notices)
                self.assertIn('Creeeeger', archive.read(builder.CREDITS_ENTRY).decode())
                self.assertIsNone(archive.testzip())
            report = builder.verify_package(package, images=images)
            self.assertEqual(report['status'], 'twrp-rom-zip-host-verified')
            self.assertFalse(report['recovery_included'])
            self.assertFalse(report['recovery_modified'])

    def test_s10plus_extreme_structure_zip_uses_actual_sizes_without_fixed_caps(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model, codename = 'SM-G975F', 'beyond2lte'
            structure = ['system', 'vendor', 'product', 'odm', 'prism', 'optics']
            images = root / 'images'
            images.mkdir()
            fs_image = bytearray(4096)
            fs_image[1024 + 0x38:1024 + 0x3A] = b'\x53\xef'
            image_names = set(structure) | {'dtb', 'dtbo', 'boot'}
            for name in builder.ORDER:
                if name not in image_names:
                    continue
                if name in structure:
                    payload = bytes(fs_image)
                elif name == 'boot':
                    payload = b'ANDROID!' + bytes(256)
                else:
                    payload = builder.DT_TABLE_MAGIC + bytes(128)
                (images / f'{name}.img').write_bytes(payload)

            records = []
            for name in builder.ORDER:
                if name not in image_names:
                    continue
                path = images / f'{name}.img'
                filesystem = name in structure
                record = {
                    'name': name,
                    'filename': path.name,
                    'role': 'filesystem-partition' if filesystem else 'boot-component',
                    'bytes': path.stat().st_size,
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'filesystem': 'ext4' if filesystem else None,
                    'sparse': False,
                }
                if not filesystem:
                    record['validation'] = 'raw-header-verified'
                records.append(record)

            raw_receipt = root / 'raw-proof.json'
            build_identity = {
                'project': 'X-NovaOS',
                'format': 'raw-images-only-v1',
                'target_model': model,
                'target_codename': codename,
                'partition_layout': 'extreme-structure',
                'partition_structure': structure,
                'automatic_installer_included': False,
                'recovery_installer_included': False,
                'flashing_method_included': False,
                'hardware_validated': False,
                'image_count': len(records),
            }
            raw_receipt.write_text(json.dumps({
                'schema_version': 1,
                'format': 'raw-images-only-v1',
                'status': 'images-built-and-host-verified',
                'target_model': model,
                'target_codename': codename,
                'partition_layout': 'extreme-structure',
                'partition_structure': structure,
                'partition_profile_caps': {},
                'required_images': [name for name in builder.ORDER if name in builder.REQUIRED],
                'contains_recovery': False,
                'contains_installer': False,
                'contains_new_dat_br': False,
                'contains_transfer_lists': False,
                'firmware_lock_sha256': 'a' * 64,
                'build': build_identity,
                'provenance': {'target': model, 'codename': codename},
                'images': records,
            }))

            output = root / 's10plus.zip'
            with self.assertRaisesRegex(ValueError, 'requires the extreme-structure receipt'):
                builder.build(
                    images, root / 'missing-proof.zip',
                    expected_model=model, expected_codename=codename,
                )
            with patch.object(builder, 'verify_image'):
                builder.build(
                    images, output, receipt=raw_receipt,
                    expected_model=model, expected_codename=codename,
                )
            report = builder.verify_package(
                output, expected_model=model, expected_codename=codename,
                images=images, raw_receipt=raw_receipt,
            )
            self.assertEqual(report['target_model'], model)
            self.assertEqual(report['target_codename'], codename)
            with zipfile.ZipFile(output) as archive:
                sizes = json.loads(archive.read('REQUIRED-IMAGE-SIZES.json'))
                self.assertEqual(sizes['partition_layout'], 'extreme-structure')
                self.assertEqual(sizes['partition_profile_caps'], {})
                self.assertEqual(sizes['partition_structure'], structure)
                self.assertEqual(
                    sizes['image_size_bytes'],
                    {record['name']: record['bytes'] for record in records},
                )
                self.assertFalse(sizes['physical_layout_verified'])
                warning = archive.read('WARNING.txt').decode().lower()
                self.assertIn('no fixed image-size cap', warning)
                self.assertIn('does not verify the physical partition table', warning)
                self.assertIn('read-only installer guard', warning)
                guard = archive.read('installer/layout-check.sh').decode()
            for name in structure + ['boot']:
                record = next(record for record in records if record['name'] == name)
                self.assertIn(f'check_partition {name} {record["bytes"]}', guard)
            self.assertNotIn('7340032000', guard)
            self.assertNotIn('1572864000', guard)
            subprocess.run(['sh', '-n'], input=guard, text=True, check=True)
            self.assertEqual(
                builder._declared_profile_caps('extreme-structure', model, codename), {},
            )
            self.assertEqual(
                builder._declared_profile_structure('extreme-structure', model, codename),
                structure,
            )

    def test_hash_failure_stops_during_staging_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, package, _, stage = self.fixtures(root)
            text = (stage / 'manifest.tsv').read_text().splitlines()
            first = text[0].split('\t'); first[2] = '0' * 64; text[0] = '\t'.join(first)
            (stage / 'manifest.tsv').write_text('\n'.join(text) + '\n')
            result = self.shell(root, package, stage, 'validate_manifest\nstage_images\ntouch "$stage/UNSAFE_WRITE_REACHED"\n')
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((stage / 'UNSAFE_WRITE_REACHED').exists())
            self.assertIn('STAGE_HASH_MISMATCH', (stage / 'log').read_text())

    def test_invalid_manifests(self):
        for change in ('duplicate', 'wrong_name', 'missing_boot', 'missing_dtb', 'wrong_hash', 'wrong_order', 'extra_field', 'zero_size'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                _, package, _, stage = self.fixtures(root)
                rows = (stage / 'manifest.tsv').read_text().splitlines()
                if change == 'duplicate': rows.insert(0, rows[0])
                if change == 'wrong_name': rows[0] = rows[0].replace('system', 'userdata', 1)
                if change == 'missing_boot': rows.pop()
                if change == 'missing_dtb': rows = [row for row in rows if not row.startswith('dtb\t')]
                if change == 'wrong_hash': rows[0] = rows[0].rsplit('\t', 1)[0] + '\tBAD'
                if change == 'wrong_order': rows.reverse()
                if change == 'extra_field': rows[0] += '\tunexpected'
                if change == 'zero_size':
                    values = rows[0].split('\t'); values[1] = '0'; rows[0] = '\t'.join(values)
                (stage / 'manifest.tsv').write_text('\n'.join(rows) + '\n')
                result = self.shell(root, package, stage, 'validate_manifest\n')
                self.assertNotEqual(result.returncode, 0)

    def test_real_chunked_write_and_readback_preserve_bytes_after_image(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); stage = root / 'stage'; stage.mkdir()
            target = root / 'targets'; target.mkdir()
            payload = b'x' * (32 * 1024 * 1024) + b'final-partial-chunk'
            (stage / 'system.img').write_bytes(payload)
            (target / 'system').write_bytes(b'Z' * (len(payload) + 31))
            digest = hashlib.sha256(payload).hexdigest()
            result = self.shell(root, root / 'unused.zip', stage, f'image_index=1; image_count=1\nwrite_one system {len(payload)} {digest}\n')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((target / 'system').read_bytes(), payload + b'Z' * 31)
            log = (stage / 'log').read_text()
            self.assertIn('32/33', log); self.assertIn('33/33', log)
            self.assertIn('Verified on target: system', log)

    def test_dd_timeout_stops_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); stage = root / 'stage'; stage.mkdir()
            targets = root / 'targets'; targets.mkdir()
            (stage / 'system.img').write_bytes(b'payload')
            (targets / 'system').write_bytes(b'unchanged')
            result = self.shell(root, root / 'unused.zip', stage, 'timeout() { return 124; }\nimage_index=1; image_count=1\nwrite_one system 7 ' + hashlib.sha256(b'payload').hexdigest() + '\n')
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((targets / 'system').read_bytes(), b'unchanged')
            self.assertIn('WRITE_CHUNK', (stage / 'log').read_text())

    def test_readback_mismatch_stops_before_following_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, package, _, stage = self.fixtures(root)
            targets = root / 'targets'; targets.mkdir()
            for name in builder.REQUIRED: (targets / name).write_bytes(b'untouched' * 100)
            result = self.shell(root, package, stage, '''validate_manifest
stage_images
# Unit harness only: production check_targets is not bypassable by an env flag.
check_targets() { :; }
timeout() { shift; if [ "$1" = head ]; then printf 'bad readback'; else command "$@"; fi; }
write_images
''')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('READBACK_HASH_MISMATCH', (stage / 'log').read_text())
            self.assertEqual((targets / 'boot').read_bytes(), b'untouched' * 100)
            self.assertEqual((targets / 'vendor').read_bytes(), b'untouched' * 100)

    def test_builder_rejects_unsafe_inputs_and_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images, package, _, _ = self.fixtures(root)
            original = package.read_bytes()
            with self.assertRaises(ValueError): builder.build(images, package)
            self.assertEqual(package.read_bytes(), original)
            (images / 'recovery.img').write_bytes(b'danger')
            with self.assertRaises(ValueError): builder.build(images, root / 'bad.zip')
            (images / 'recovery.img').unlink()
            with self.assertRaises(ValueError): builder.build(images, root / 'bad.zip', '/dev/block/../../data')

    def test_builder_removes_partial_package_on_failed_fsck(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images, _, _, _ = self.fixtures(root)
            output = root / 'bad.zip'
            with patch.object(builder, 'verify_image', side_effect=ValueError('bad filesystem')):
                with self.assertRaises(ValueError): builder.build(images, output)
            self.assertFalse(output.exists())

    def test_runtime_has_hardware_safety_gates_and_no_test_bypass(self):
        entry = (ROOT / 'integration/new_installer/update-binary.sh').read_text()
        self.assertIn('ro.boot.em.model', entry)
        self.assertIn('BATTERY_LOW_CHARGE_FIRST', entry)
        self.assertIn('DATA_NOT_MOUNTED', entry)
        self.assertIn('DD_SELF_TEST', entry)
        self.assertIn('ZIP64_PROBE', entry)
        self.assertLess(entry.index('stage_images'), entry.index('write_images'))
        self.assertNotIn('ALLOW_REGULAR', entry)
        for file in (ENGINE, ROOT / 'integration/new_installer/update-binary.sh'):
            subprocess.run(['sh', '-n', str(file)], check=True)

    def test_standalone_probe_never_targets_a_device(self):
        path = ROOT / 'integration/new_installer/probe-recovery.sh'
        text = path.read_text()
        self.assertNotIn('of=/dev/', text)
        self.assertNotIn('write_images', text)
        self.assertNotIn('mkfs', text)
        self.assertIn('of="$work/output"', text)
        subprocess.run(['sh', '-n', str(path)], check=True)


if __name__ == '__main__':
    unittest.main()
