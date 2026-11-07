"""Exercise the transformed REAL helper used by download and extraction."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('descriptor_prepare',ROOT/'scripts/prepare_workspace.py')
prepare=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepare)


class FirmwareDescriptorTests(unittest.TestCase):
    def parse(self,descriptor):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);utils=root/'scripts/utils';utils.mkdir(parents=True)
            target=utils/'firmware_utils.sh';target.write_bytes((ROOT/'reference/build/scripts/utils/firmware_utils.sh').read_bytes())
            (utils/'build_utils.sh').write_text('LOGE() { printf "%s\\n" "$*" >&2; };\n')
            prepare.patch_firmware_lookup(root)
            subprocess.run(['bash','-n',str(target)],check=True)
            command='SRC_DIR="$1"; source "$1/scripts/utils/firmware_utils.sh" || exit 1; IMEI=STALE; SERIAL_NO=STALE; PARSE_FIRMWARE_STRING "$2"; status=$?; printf "%s|%s|%s|%s|%s" "$status" "$MODEL" "$CSC" "$IMEI" "$SERIAL_NO"; exit "$status"'
            return subprocess.run(['bash','-c',command,'test',str(root),descriptor],capture_output=True,text=True)

    def test_exact_s24fe_descriptor_from_failed_diagnostic(self):
        result=self.parse('SM-S721B/EUX/S721BXXSFEZJ1')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,'0|SM-S721B|EUX||')

    def test_two_part_descriptor_requires_no_identifier(self):
        result=self.parse('SM-S721B/EUX')
        self.assertEqual(result.stdout,'0|SM-S721B|EUX||')
        self.assertEqual(result.returncode,0)

    def test_legacy_target_third_token_is_ignored_not_forwarded(self):
        # Synthetic token, not an actual user's device identifier.
        result=self.parse('SM-G973F/AUT/00000000')
        self.assertEqual(result.returncode,0)
        self.assertEqual(result.stdout,'0|SM-G973F|AUT||')
        self.assertNotIn('00000000',result.stdout+result.stderr)

    def test_invalid_descriptors_clear_state_without_echoing_sensitive_input(self):
        for text in ('','SM-S721B','SM-S721B/EU','../EUX','SM-S721B/EUX/AP/EXTRA','SM-S721B/EUX/','SM-S721B/EUX/secret;echo BAD'):
            with self.subTest(descriptor=text):
                result=self.parse(text)
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(result.stdout,'1||||')
                self.assertNotIn('STALE',result.stdout+result.stderr)
                self.assertNotIn('secret',result.stderr)
