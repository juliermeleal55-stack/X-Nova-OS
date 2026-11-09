import io
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from integration import installer_integrity as integrity
from integration.build_policy import zip_policy
from scripts.publish_alpha3 import release_notes

ROOT = Path(__file__).resolve().parents[1]


class InstallerIntegrityTests(unittest.TestCase):
    def test_rejects_non_artisan_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'prebuilts/bootable/deprecated-ota/updater'
            path.parent.mkdir(parents=True)
            path.write_bytes(b'not-the-updater')
            with self.assertRaisesRegex(ValueError, 'pinned ArtisanROM'):
                integrity.verify_updater(root)

    def test_erofs_check_reads_all_file_encodings_without_extract_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / 'system.img'
            data = bytearray(4096)
            struct.pack_into('<I', data, 1024, integrity.EROFS_MAGIC)
            image.write_bytes(data)
            with patch.object(integrity.subprocess, 'run') as run:
                report = integrity.verify_image(image)
            run.assert_called_once_with(['fsck.erofs', '--extract', str(image)], check=True)
            self.assertEqual(report['filesystem'], 'erofs')
            self.assertEqual(image.read_bytes(), data)

    def test_fsck_failure_blocks_packaging(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / 'system.img'
            data = bytearray(4096)
            struct.pack_into('<I', data, 1024, integrity.EROFS_MAGIC)
            image.write_bytes(data)
            with patch.object(integrity.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'fsck')):
                with self.assertRaises(subprocess.CalledProcessError):
                    integrity.verify_image(image)

    def test_unknown_filesystem_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / 'system.img'
            image.write_bytes(bytes(4096))
            with self.assertRaisesRegex(ValueError, 'Unrecognized'):
                integrity.verify_image(image)

    def test_sparse_conversion_failure_blocks_and_removes_temporary_files(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / 'system.img'
            image.write_bytes(struct.pack('<I', integrity.SPARSE_MAGIC))
            with patch.object(integrity.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'simg2img')):
                with self.assertRaises(subprocess.CalledProcessError):
                    integrity.verify_image(image)
            self.assertEqual(list(Path(directory).iterdir()), [image])

    def brotli_check(self, expected, decoded, code=0):
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / 'system.new.dat'
            original.write_bytes(expected)
            process = MagicMock()
            process.stdout = io.BytesIO(decoded)
            process.wait.return_value = code
            process.__enter__.return_value = process
            with patch.object(integrity.subprocess, 'Popen', return_value=process):
                return integrity.verify_brotli(Path(directory) / 'data.br', original)

    def test_brotli_roundtrip_positive(self):
        self.assertEqual(self.brotli_check(b'payload', b'payload')['new_dat_bytes'], 7)

    def test_brotli_mismatch_truncation_extra_and_decoder_failure(self):
        for expected, decoded, code in [(b'abc', b'axc', 0), (b'abc', b'ab', 0),
                                        (b'ab', b'abc', 0), (b'abc', b'abc', 1)]:
            with self.subTest(decoded=decoded, code=code), self.assertRaises(ValueError):
                self.brotli_check(expected, decoded, code)

    def test_generated_script_checks_before_deleting_original_payload(self):
        text = zip_policy((ROOT / 'reference/build/scripts/internal/build_flashable_zip.sh').read_text())
        self.assertLess(text.index('installer_integrity.py" image'), text.index('EVAL "img2sdat'))
        self.assertLess(text.index('installer_integrity.py" brotli'), text.index('rm -f "$TMP_DIR/$PARTITION.new.dat"'))
        self.assertLess(text.index('installer_integrity.py" updater'), text.index('cp -a "$SRC_DIR/prebuilts/bootable'))
        self.assertIn('for mountpoint in /system /system_root', text)
        self.assertIn('system write completed.', text)

    def test_release_refuses_expired_or_empty_artifacts(self):
        for artifact in [{'expired': True, 'size_in_bytes': 1}, {'expired': False, 'size_in_bytes': 0}]:
            with self.assertRaises(ValueError):
                release_notes(artifact, 'owner/repo', '1', 'sha')

    def test_release_links_whole_artifact_without_claiming_boot_fix(self):
        notes = release_notes({'id': 123, 'name': 'rom', 'size_in_bytes': 6000000000,
                               'expires_at': 'date', 'digest': 'sha256:test'}, 'owner/repo', '42', 'abc')
        self.assertIn('/actions/runs/42/artifacts/123', notes)
        self.assertIn('não foi comprovada', notes)
        self.assertIn('não do ZIP interno', notes)


if __name__ == '__main__':
    unittest.main()
