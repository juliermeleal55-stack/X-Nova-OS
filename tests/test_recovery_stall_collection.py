import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location('stall_collector', Path(__file__).resolve().parents[1] / 'scripts/collect_recovery_stall.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class RecoveryStallCollectionTests(unittest.TestCase):
    def test_missing_logs_do_not_prevent_other_evidence(self):
        commands = []

        def fake_capture(adb, args):
            commands.append(args)
            if args == ['get-state']:
                return 0, b'recovery\n', ''
            if '/cache/' in args[-1]:
                return 1, b'', 'No such file'
            return 0, b'sample evidence\n', ''

        with tempfile.TemporaryDirectory() as root, patch.object(collector, 'capture', side_effect=fake_capture), patch.object(collector.time, 'sleep'):
            archive = collector.collect('adb', Path(root) / 'output')
            with zipfile.ZipFile(archive) as handle:
                self.assertIn('recovery-final.log', handle.namelist())
                self.assertIn('2-diskstats.txt', handle.namelist())
                manifest = json.loads(handle.read('collection.json'))
                self.assertEqual(manifest['results']['cache-last_log.txt']['exit_code'], 1)
        permitted = set(collector.COMMANDS.values()) | {'cat ' + path for path in collector.FILES.values()}
        for args in commands:
            self.assertTrue(args == ['get-state'] or (args[0] == 'shell' and args[1] in permitted))

    def test_absent_device_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as root, patch.object(collector, 'capture', return_value=(1, b'', 'no device')):
            destination = Path(root) / 'output'
            with self.assertRaises(RuntimeError):
                collector.collect('adb', destination)
            self.assertFalse(destination.exists())

    def test_timeout_is_recorded(self):
        with patch.object(collector.subprocess, 'run', side_effect=collector.subprocess.TimeoutExpired('adb', 30)):
            code, output, error = collector.capture('adb', ['shell', 'dmesg'])
        self.assertEqual(code, 124)
        self.assertEqual(output, b'')
        self.assertIn('timed out', error)

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as root, patch.object(collector, 'capture', return_value=(0, b'recovery', '')):
            with self.assertRaises(FileExistsError):
                collector.collect('adb', Path(root))


if __name__ == '__main__':
    unittest.main()
