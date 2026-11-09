import io
import json
import struct
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

from integration import dex_container_probe as probe


def unit(version, classes, size=0x80, container=0, offset=0):
    header = 0x78 if version >= 41 else 0x70
    data = bytearray(size)
    data[0:8] = b'dex\n%03d\x00' % version
    struct.pack_into('<II', data, 0x20, size, header)
    struct.pack_into('<I', data, 0x60, classes)
    struct.pack_into('<I', data, 0x28, 0x12345678)
    if version >= 41:
        struct.pack_into('<II', data, 0x70, container, offset)
    return data


def container(class_counts, wrong_total=None, wrong_offset=None):
    size, total = 0x80, 0x80 * len(class_counts)
    out = bytearray()
    for index, count in enumerate(class_counts):
        offset = size * index if wrong_offset is None or index != 1 else wrong_offset
        out += unit(41, count, size, wrong_total or total, offset)
    return bytes(out)


class ProbeTests(unittest.TestCase):
    def test_single_dex_v039(self):
        found = probe.units(bytes(unit(39, 7)))
        self.assertEqual([(u['version'], u['class_defs']) for u in found], [(39, 7)])

    def test_container_041_lists_every_logical_unit(self):
        found = probe.units(container([10, 20, 30]))
        self.assertEqual([u['class_defs'] for u in found], [10, 20, 30])
        self.assertEqual([u['offset'] for u in found], [0, 0x80, 0x100])

    def test_bad_container_size_fails_loudly(self):
        with self.assertRaises(ValueError):
            probe.units(container([1, 2], wrong_total=999))

    def test_bad_header_offset_fails_loudly(self):
        with self.assertRaises(ValueError):
            probe.units(container([1, 2, 3], wrong_offset=5))

    def test_garbage_after_first_unit_fails_loudly(self):
        data = bytearray(container([1, 2]))
        data[0x80:0x88] = b'GARBAGE!'
        with self.assertRaises(ValueError):
            probe.units(bytes(data))

    def test_truncated_single_dex_fails(self):
        with self.assertRaises(ValueError):
            probe.units(bytes(unit(39, 1, size=0x80))[:0x40])

    def _jar(self, root):
        path = Path(root) / 'services.jar'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('classes.dex', container([5, 6]))
            archive.writestr('classes2.dex', bytes(unit(39, 4)))
            archive.writestr('META-INF/MANIFEST.MF', 'x')
        return path

    def test_zip_reports_physical_entries_in_order(self):
        with tempfile.TemporaryDirectory() as root:
            entries = probe.inspect(self._jar(root))
        self.assertEqual([(e['entry'], e['logical_units'], e['class_defs']) for e in entries],
                         [('classes.dex', 2, 11), ('classes2.dex', 1, 4)])

    def test_cli_detects_missing_decoded_classes(self):
        with tempfile.TemporaryDirectory() as root:
            jar = self._jar(root)
            smali = Path(root) / 'out'
            (smali / 'smali').mkdir(parents=True)
            for index in range(5):  # so a primeira unidade foi decodificada
                (smali / 'smali' / f'C{index}.smali').write_text('.class LC;')
            out = io.StringIO()
            with redirect_stdout(out):
                code = probe.main([str(jar), '--smali-dir', str(smali)])
            report = json.loads(out.getvalue())
        self.assertEqual(code, 2)
        self.assertEqual((report['total_class_defs'], report['decoded_smali_files']), (15, 5))
        self.assertTrue(report['mismatch'])

    def test_cli_ok_when_counts_match(self):
        with tempfile.TemporaryDirectory() as root:
            jar = self._jar(root)
            smali = Path(root) / 'out'
            (smali / 'smali_classes2').mkdir(parents=True)
            for index in range(15):
                (smali / 'smali_classes2' / f'C{index}.smali').write_text('.class LC;')
            with redirect_stdout(io.StringIO()):
                self.assertEqual(probe.main([str(jar), '--smali-dir', str(smali)]), 0)

    def test_invalid_file_returns_1(self):
        with tempfile.TemporaryDirectory() as root:
            bad = Path(root) / 'x.dex'
            bad.write_bytes(b'not a dex file at all' * 10)
            self.assertEqual(probe.main([str(bad)]), 1)


class HardenedProbeTests(unittest.TestCase):
    def test_rejects_invalid_legacy_sizes_and_unknown_versions(self):
        for version, file_size, header_size in [(39, 0, 0), (39, 0x80, 0x78), (36, 0x80, 0x70), (42, 0x80, 0x78)]:
            data = unit(version, 0)
            struct.pack_into('<II', data, 0x20, file_size, header_size)
            with self.subTest(version=version, header=header_size), self.assertRaises(ValueError):
                probe.units(bytes(data))

    def test_valid_040_header_is_supported(self):
        self.assertEqual(probe.units(bytes(unit(40, 1)))[0]['version'], 40)

    def test_rejects_trailing_legacy_bytes_and_wrong_endian(self):
        with self.assertRaises(ValueError):
            probe.units(bytes(unit(39, 1)) + b'extra')
        data = unit(39, 1)
        struct.pack_into('<I', data, 0x28, 0)
        with self.assertRaises(ValueError):
            probe.units(bytes(data))

    def test_empty_and_duplicate_dex_archives_rejected(self):
        for names in [('assets/data',), ('classes.dex', 'classes.dex'), ('classes2.dex',)]:
            with tempfile.TemporaryDirectory() as root:
                path = Path(root) / 'input.jar'
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    with zipfile.ZipFile(path, 'w') as archive:
                        for name in names:
                            archive.writestr(name, bytes(unit(39, 0)))
                with self.assertRaises(ValueError):
                    probe.inspect(path)

    def test_mapping_checks_counts_per_unit_not_only_total(self):
        entries = [{'entry': 'classes.dex', 'units': [{'class_defs': 1}, {'class_defs': 2}]}]
        mapping = {'schema_version': 1, 'units': [
            {'entry': 'classes.dex', 'smali': 'smali', 'output': 'classes.dex'},
            {'entry': 'classes.dex/2', 'smali': 'smali_classes2', 'output': 'classes2.dex'}]}
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            for directory, count in [('smali', 2), ('smali_classes2', 1)]:
                (root / directory).mkdir()
                for i in range(count):
                    (root / directory / f'C{i}.smali').write_text('.class LC;')
            with self.assertRaisesRegex(ValueError, 'Contagem independente'):
                probe.verify_mapping(entries, root, mapping)
            (root / 'smali' / 'C1.smali').rename(root / 'smali_classes2' / 'C1.smali')
            self.assertEqual(probe.verify_mapping(entries, root, mapping)['total_class_defs'], 3)
            mapping['units'][1]['entry'] = 'classes.dex/3'
            with self.assertRaisesRegex(ValueError, 'Mapa baksmali'):
                probe.verify_mapping(entries, root, mapping)

    def test_missing_smali_is_controlled_cli_error(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'a.dex'
            path.write_bytes(unit(39, 1))
            self.assertEqual(probe.main([str(path), '--smali-dir', str(Path(root) / 'absent')]), 1)

    def test_production_cli_runs_independent_check(self):
        from integration import dex_entries
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            source = root / 'input.jar'
            with zipfile.ZipFile(source, 'w') as archive:
                archive.writestr('classes.dex', unit(39, 1))
            decoded = root / 'out'
            (decoded / 'smali').mkdir(parents=True)
            mapping = {'schema_version': 1, 'units': [{'entry': 'classes.dex', 'smali': 'smali', 'output': 'classes.dex'}]}
            (decoded / dex_entries.MAP).write_text(json.dumps(mapping))
            # Empty decoded directory must fail BEFORE the baksmali-dependent verifier.
            with patch('sys.argv', ['dex_entries.py', 'verify-decode', str(source), str(decoded)]), patch.object(dex_entries, 'verify_decode') as verify:
                with self.assertRaisesRegex(ValueError, 'Contagem independente'):
                    dex_entries.main()
                verify.assert_not_called()
            (decoded / 'smali' / 'C.smali').write_text('.class LC;')
            with patch('sys.argv', ['dex_entries.py', 'verify-decode', str(source), str(decoded), str(root / 'evidence')]), patch.object(dex_entries, 'verify_decode') as verify:
                dex_entries.main()
                verify.assert_called_once()
            report = json.loads(next((root / 'evidence').glob('*-independent.json')).read_text())
            self.assertEqual(report['total_class_defs'], 1)
            self.assertEqual(len(report['source_sha256']), 64)


if __name__ == '__main__':
    unittest.main()
