"""Boundary tests: actual pinned copier with a synthetic rsync shim, not firmware."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from integration.firmware_check import inspect,system_ext_layout
from test_s24fe_donor import donor_fixture

ROOT=Path(__file__).resolve().parents[1]


class EmbeddedDonorPipelineTests(unittest.TestCase):
    def test_embedded_system_ext_is_valid_with_no_separate_partition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);donor_fixture(root)
            (root/'out/fw/SM-S721B_EUX/system/system/system_ext').mkdir()
            result=inspect(root)
            source=result['firmwares'][0]
            self.assertEqual(source['system_ext_layout'],'embedded')
            self.assertFalse(source['separate_system_ext'])
            self.assertTrue(source['embedded_system_ext'])

    def test_alias_to_same_embedded_tree_is_not_an_extra_partition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);embedded=root/'system/system/system_ext';embedded.mkdir(parents=True)
            (root/'system_ext').symlink_to('system/system/system_ext',target_is_directory=True)
            result=system_ext_layout(root)
            self.assertEqual(result['system_ext_layout'],'embedded')
            self.assertTrue(result['system_ext_alias'])

    def test_independent_double_layout_and_escaping_alias_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'system/system/system_ext').mkdir(parents=True)
            (root/'system_ext').mkdir()
            with self.assertRaisesRegex(ValueError,'Ambiguous'):system_ext_layout(root)
            (root/'system_ext').rmdir();(root/'system_ext').symlink_to('/tmp')
            with self.assertRaisesRegex(ValueError,'Unsafe'):system_ext_layout(root)

    def test_failed_sdk_inspection_preserves_actual_values_and_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);donor_fixture(root)
            (root/'out/fw/SM-S721B_EUX/system/system/build.prop').write_text('ro.build.version.sdk=36\nro.build.version.release=16\nro.build.version.oneui=80000\n')
            with self.assertRaisesRegex(ValueError,'actual SDK=36'):inspect(root)
            result=json.loads((root/'out/beyoud-firmware-inspection.json').read_text())
            self.assertEqual(result['status'],'blocked')
            self.assertEqual(result['firmwares'][0]['sdk'],36)
            self.assertEqual(result['firmwares'][0]['ro.build.version.oneui'],'80000')
            self.assertIn('actual SDK=36',result['error'])

    def test_original_artisan_copier_preserves_embedded_systemui_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'fw/source';work=root/'work';tools=root/'bin'
            payload=source/'system/system/system_ext/priv-app/SystemUI/SystemUI.apk'
            payload.parent.mkdir(parents=True);payload.write_bytes(b'SYNTHETIC-NOT-AN-APK')
            (source/'system/system/build.prop').write_text('ro.build.version.sdk=37\n')
            (source/'fs_config-system').write_text('system 0 0 755\nsystem/system_ext 0 0 755\nsystem/system_ext/priv-app/SystemUI/SystemUI.apk 0 0 644\n')
            (source/'file_context-system').write_text('/system u:object_r:system_file:s0\n/system/system_ext/priv-app/SystemUI/SystemUI.apk u:object_r:system_file:s0\n')
            (work/'configs').mkdir(parents=True);tools.mkdir()
            # Deliberately synthetic shim: only directory-copy/exclude semantics.
            shim=tools/'rsync';shim.write_text('#!/usr/bin/env python3\nimport pathlib,shutil,sys\nsrc,dst=map(pathlib.Path,sys.argv[-2:])\ndst.mkdir(parents=True,exist_ok=True)\nignore=shutil.ignore_patterns("*system_ext*") if any(a.startswith("--exclude=") for a in sys.argv) else None\nshutil.copytree(src,dst/src.name,dirs_exist_ok=True,ignore=ignore)\n');shim.chmod(0o755)
            raw=(ROOT/'reference/build/scripts/internal/create_work_dir.sh').read_text()
            function=raw[raw.index('COPY_SOURCE_FIRMWARE()'):raw.index('\nCOPY_TARGET_FIRMWARE()')]
            script='set -e\nLOG() { :; }; LOG_STEP_IN() { :; }; LOG_STEP_OUT() { :; }; EVAL() { eval "$1"; };\n'+function+'\nCOPY_SOURCE_FIRMWARE\n'
            result=subprocess.run(['bash','-c',script],env=dict(os.environ,PATH=str(tools)+':'+os.environ['PATH'],FW_DIR=str(root/'fw'),SOURCE_FIRMWARE_PATH='source',WORK_DIR=str(work),TARGET_HAS_SYSTEM_EXT='false'),capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual((work/'system/system/system_ext/priv-app/SystemUI/SystemUI.apk').read_bytes(),b'SYNTHETIC-NOT-AN-APK')
            self.assertEqual((work/'system/system_ext').readlink(),Path('/system/system_ext'))
            self.assertIn('system/system_ext/priv-app/SystemUI/SystemUI.apk',(work/'configs/fs_config-system').read_text())
            self.assertFalse((work/'system_ext').exists())
