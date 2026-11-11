import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from integration.s10_compat import (
    donor_sdk,
    guard_legacy_bluetooth,
    initialize_legacy_vendor,
    install,
)

ROOT = Path(__file__).resolve().parents[1]
MISCS = ROOT / 'reference/artisan-s10/platform/exynos9820/patches/miscs/customize.sh'


class S10CompatibilityTests(unittest.TestCase):
    def stock(self, root):
        for relative, content in {
            'system/system/etc/ueventd.rc': '# system rules\n',
            'vendor/ueventd.rc': '# stock vendor rules\n',
            'vendor/etc/selinux/vendor_property_contexts':
                'vendor.existing u:object_r:vendor_default_prop:s0',
            'vendor/etc/selinux/vendor_sepolicy.cil': '(type vendor_rild_prop)\n',
        }.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    def test_donor_sdk_is_read_from_extracted_s24fe_properties(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prop = root / 'SM-S721B_EUX/system/system/build.prop'
            prop.parent.mkdir(parents=True)
            prop.write_text('ro.build.version.sdk=37\n')
            self.assertEqual(donor_sdk(root, 'SM-S721B/EUX/S721BXXSFEZJ1'), 37)
            prop.write_text('ro.build.version.sdk=37\nro.build.version.sdk=36\n')
            with self.assertRaisesRegex(ValueError, 'exactly one'):
                donor_sdk(root, 'SM-S721B/EUX/S721BXXSFEZJ1')
            with self.assertRaises(ValueError):
                donor_sdk(root, '../EUX/AP')

    def test_bluetooth_guard_uses_actual_sdk_and_preserves_old_branch_only(self):
        original = MISCS.read_text()
        guarded = guard_legacy_bluetooth(original)
        subprocess.run(['bash', '-n'], input=guarded, text=True, check=True)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prop = root / 'fw/SM-S721B_EUX/system/system/build.prop'
            prop.parent.mkdir(parents=True)
            prop.write_text('ro.build.version.sdk=37\n')
            library = root / 'work/system/system/lib64/libbluetooth_jni.so'
            library.parent.mkdir(parents=True)
            library.touch()
            snippet = guarded[guarded.index('_BEYOUD_DONOR_SDK='):]
            script = root / 'bluetooth-guard.sh'
            script.write_text(
                'ADD_TO_WORK_DIR() { echo OLD_APEX; };\n'
                'HEX_PATCH() { echo OLD_HEX; };\n'
                'LOG_STEP_OUT() { :; };\n' + snippet
            )
            env = dict(os.environ, SRC_DIR=str(ROOT), FW_DIR=str(root / 'fw'),
                       WORK_DIR=str(root / 'work'),
                       SOURCE_FIRMWARE='SM-S721B/EUX/S721BXXSFEZJ1',
                       SOURCE_API_LEVEL='36')
            for actual_sdk, expected in ((36, 'OLD_APEX\nOLD_HEX\n'), (37, '')):
                prop.write_text(f'ro.build.version.sdk={actual_sdk}\n')
                result = subprocess.run(['bash', str(script)], env=env, text=True,
                                        capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected)
        with self.assertRaises(ValueError):
            guard_legacy_bluetooth(original.replace('289767394805003736008052', 'changed'))

    def test_onerom_bluetooth_schema_uses_the_extracted_donor_sdk(self):
        from integration.s10_compat import APEX_IMPORT, BT_PATCH_TAILS, SOURCE_SDK_GATE
        upstream = (ROOT / 'reference/onerom-port-candidates/source-snapshot/'
                    'platform/exynos9820/patches/miscs/customize.sh').read_text()
        guarded_upstream = guard_legacy_bluetooth(upstream)
        self.assertNotIn(SOURCE_SDK_GATE, guarded_upstream)
        self.assertEqual(guarded_upstream.count('if (( _BEYOUD_DONOR_SDK < 37 )); then'), 2)
        self.assertEqual(guarded_upstream.count('ro.build.version.sdk'), 0)
        subprocess.run(['bash', '-n'], input=guarded_upstream, text=True, check=True)

        tail = BT_PATCH_TAILS[1]
        synthetic = (
            SOURCE_SDK_GATE + "\n    " + APEX_IMPORT + "\nfi\n"
            + "# BT-lib-patch\n" + SOURCE_SDK_GATE + "\n"
            + 'HEX_PATCH "$WORK_DIR/system/system/lib64/libbluetooth_jni.so" '
            + chr(92) + "\n" + tail + "\nfi\n"
        )
        guarded = guard_legacy_bluetooth(synthetic)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prop = root / 'fw/SM-S721B_EUX/system/system/build.prop'
            prop.parent.mkdir(parents=True)
            prop.write_text('ro.build.version.sdk=37\n')
            script = root / 'bluetooth-guard.sh'
            script.write_text(
                'ADD_TO_WORK_DIR() { echo OLD_APEX; };\n'
                'HEX_PATCH() { echo OLD_HEX; };\n' + guarded
            )
            env = dict(os.environ, SRC_DIR=str(ROOT), FW_DIR=str(root / 'fw'),
                       WORK_DIR=str(root / 'work'),
                       SOURCE_FIRMWARE='SM-S721B/EUX/S721BXXSFEZJ1')
            for actual_sdk, expected in ((36, 'OLD_APEX\nOLD_HEX\n'), (37, '')):
                prop.write_text(f'ro.build.version.sdk={actual_sdk}\n')
                result = subprocess.run(['bash', str(script)], env=env, text=True,
                                        capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected)

    def test_vendor_init_is_idempotent_and_keeps_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.stock(root)
            contexts = root / 'vendor/etc/selinux/vendor_property_contexts'
            contexts.chmod(0o640)
            initialize_legacy_vendor(root)
            once = contexts.read_bytes()
            initialize_legacy_vendor(root)
            self.assertEqual(once, contexts.read_bytes())
            self.assertIn(b'vendor.sec.rild.libpath ', once)
            self.assertEqual(contexts.stat().st_mode & 0o777, 0o640)
            self.assertEqual((root / 'system/system/etc/ueventd.rc').read_text().count(
                'import /vendor/ueventd.rc'), 1)

    def test_existing_vendor_mapping_and_import_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.stock(root)
            contexts = root / 'vendor/etc/selinux/vendor_property_contexts'
            contexts.write_text('vendor.sec.rild.libpath u:object_r:other_prop:s0\n')
            (root / 'system/system/etc/ueventd.rc').write_text(
                '  import /vendor/ueventd.rc # stock\n')
            initialize_legacy_vendor(root)
            self.assertEqual(contexts.read_text(),
                             'vendor.sec.rild.libpath u:object_r:other_prop:s0\n')
            self.assertEqual((root / 'system/system/etc/ueventd.rc').read_text().count('import'), 1)

    def test_missing_input_fails_before_mutating_other_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.stock(root)
            (root / 'vendor/etc/selinux/vendor_sepolicy.cil').unlink()
            ueventd = root / 'system/system/etc/ueventd.rc'
            before = ueventd.read_bytes()
            with self.assertRaises(ValueError):
                initialize_legacy_vendor(root)
            self.assertEqual(ueventd.read_bytes(), before)

    def test_unknown_policy_type_is_not_invented(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.stock(root)
            (root / 'vendor/etc/selinux/vendor_sepolicy.cil').write_text('(type other_prop)')
            initialize_legacy_vendor(root)
            contexts = (root / 'vendor/etc/selinux/vendor_property_contexts').read_text()
            self.assertNotIn('vendor.sec.rild.libpath', contexts)
            self.assertTrue(contexts.endswith('\n'))

    def test_workspace_install_is_scoped_and_creates_only_project_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            customize = root / 'platform/exynos9820/patches/miscs/customize.sh'
            customize.parent.mkdir(parents=True)
            customize.write_text(MISCS.read_text())
            result = install(root, 'beyond1lte')
            self.assertEqual(result['target'], 'beyond1lte')
            self.assertFalse(result['disabled_candidates'])
            self.assertFalse(result['boot_validated'])
            module = root / 'platform/exynos9820/patches/zz_xnova_legacy_init'
            self.assertTrue((module / 'customize.sh').is_file())
            self.assertIn('integration/s10_compat.py', (module / 'customize.sh').read_text())
            self.assertIn('SDK < 37', result['active'][0])
            self.assertFalse((root / 'target/beyond1lte/patches').exists())

    def test_install_collision_fails_without_changing_artisan_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            customize = root / 'platform/exynos9820/patches/miscs/customize.sh'
            customize.parent.mkdir(parents=True)
            customize.write_text(MISCS.read_text())
            module = root / 'platform/exynos9820/patches/zz_xnova_legacy_init'
            module.mkdir()
            before = customize.read_bytes()
            with self.assertRaises(ValueError):
                install(root, 'beyond1lte')
            self.assertEqual(customize.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
