"""Real ZIP/hash/file-IO tests; NO device node, recovery or actual image flashed."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from scripts import build_raw_installer as builder

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'integration/new_installer/engine.sh'


class RawInstallerTests(unittest.TestCase):
    def fixtures(self, root):
        images = root / 'images'
        images.mkdir()
        for name in builder.REQUIRED:
            header = b'ANDROID!' if name == 'boot' else bytes.fromhex('d7b7ab1e') if name == 'dtbo' else b'fixture-not-real-filesystem'
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
                self.assertEqual(archive.read('installer/zip64-probe.txt'), b'XNOVA_RAW_V1\n')
                self.assertIsNone(archive.testzip())

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
        for change in ('duplicate', 'wrong_name', 'missing_boot', 'wrong_hash', 'wrong_order', 'extra_field', 'zero_size'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                _, package, _, stage = self.fixtures(root)
                rows = (stage / 'manifest.tsv').read_text().splitlines()
                if change == 'duplicate': rows.insert(0, rows[0])
                if change == 'wrong_name': rows[0] = rows[0].replace('system', 'userdata', 1)
                if change == 'missing_boot': rows.pop()
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
