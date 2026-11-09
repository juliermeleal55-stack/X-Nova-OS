"""Synthetic recovery environments; no device nodes are written or formatted."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
HELPER=(ROOT/'integration/recovery_layout_check.sh').read_text()


class RecoveryCapacityTests(unittest.TestCase):
    def run_check(self, overrides, checks):
        with tempfile.TemporaryDirectory() as tmp:
            script='PARTITION_CHECK_LOG='+tmp+'/check.log\n'+HELPER+'\nmount_table() { echo none /synthetic-test tmpfs rw 0 0; }\n'+overrides+'\n'+checks+'\nexit "$failures"\n'
            result=subprocess.run(['sh','-s','--','/dev/block/test-by-name'],input=script,text=True,capture_output=True)
            log=(Path(tmp)/'check.log').read_text()
            return result,log

    def test_large_decimal_comparison_without_shell_integer_overflow(self):
        pairs=[('16106127360','8481766531',True),('4294967295','4294967296',False),
               ('1572864000','1572864000',True),('0009','10',False),('00010','9',True)]
        for left,right,expected in pairs:
            with self.subTest(left=left,right=right):
                result,_=self.run_check('',f'decimal_ge {left} {right} || failures=1')
                self.assertEqual(result.returncode==0,expected)

    def test_large_system_passes_and_logs_actual_required_and_path(self):
        result,log=self.run_check('is_block() { return 0; }; blockdev() { echo 16106127360; }',
                                 'check_partition system 8481766531 || failures=1')
        self.assertEqual(result.returncode,0)
        self.assertIn('OK partition=system',log);self.assertIn('actual_bytes=16106127360',log)
        self.assertIn('required_bytes=8481766531',log);self.assertIn('/dev/block/test-by-name/system',log)

    def test_small_product_and_missing_odm_are_distinct_and_both_logged(self):
        result,log=self.run_check('is_block() { case "$1" in */odm) return 1;; esac; }; blockdev() { echo 100; }',
                                 'check_partition product 200 || failures=1\ncheck_partition odm 50 || failures=1')
        self.assertEqual(result.returncode,1)
        self.assertIn('ERR_TOO_SMALL partition=product',log)
        self.assertIn('ERR_MISSING partition=odm',log)

    def test_missing_blockdev_falls_back_to_busybox(self):
        result,log=self.run_check('is_block() { return 0; }; blockdev() { return 127; }; busybox() { echo 16106127360; }',
                                 'check_partition system 8481766531 || failures=1')
        self.assertEqual(result.returncode,0);self.assertIn('reader=busybox',log)

    def test_invalid_blockdev_output_falls_back_to_toybox(self):
        result,log=self.run_check('is_block() { return 0; }; blockdev() { echo invalid; }; busybox() { return 1; }; toybox() { echo 16106127360; }',
                                 'check_partition system 8481766531 || failures=1')
        self.assertEqual(result.returncode,0);self.assertIn('reader=toybox',log)

    def test_sysfs_fallback_converts_512_byte_sectors(self):
        result,log=self.run_check('is_block() { return 0; }; blockdev() { return 1; }; busybox() { return 1; }; toybox() { return 1; }; readlink() { echo /dev/block/sda1; }; cat() { echo 31457280; }',
                                 'check_partition system 8481766531 || failures=1')
        self.assertEqual(result.returncode,0);self.assertIn('reader=sysfs',log)
        self.assertIn('actual_bytes=16106127360',log)

    def test_unreadable_capacity_is_not_reported_as_too_small(self):
        result,log=self.run_check('is_block() { return 0; }; blockdev() { return 1; }; busybox() { return 1; }; toybox() { return 1; }; readlink() { return 1; }',
                                 'check_partition system 8481766531 || failures=1')
        self.assertEqual(result.returncode,1);self.assertIn('ERR_READ partition=system',log)
        self.assertNotIn('ERR_TOO_SMALL',log)

    def test_mounted_target_is_blocked_even_with_sufficient_capacity(self):
        result,log=self.run_check('is_block() { return 0; }; blockdev() { echo 16106127360; }; mount_table() { echo "/dev/block/sda25 /system_root erofs ro 0 0"; }; mount_source_matches() { return 0; }',
                                 'check_partition system 8481766531 || failures=1')
        self.assertEqual(result.returncode,1)
        self.assertIn('ERR_MOUNTED partition=system',log)
        self.assertNotIn('OK partition=system',log)

    def test_unreadable_mount_table_is_blocked_not_treated_as_unmounted(self):
        result,log=self.run_check('is_block() { return 0; }; blockdev() { echo 16106127360; }; mount_table() { return 1; }',
                                 'check_partition system 8481766531 || failures=1')
        self.assertEqual(result.returncode,1)
        self.assertIn('ERR_MOUNT_READ partition=system',log)

    def test_package_rejects_duplicate_installer_paths(self):
        from test_alpha import alpha,package
        import warnings
        import zipfile
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'rom.zip';package(path)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                with zipfile.ZipFile(path,'a') as archive:
                    archive.writestr('META-INF/com/google/android/updater-script','duplicate')
            with self.assertRaisesRegex(ValueError,'Duplicate ZIP entries'):alpha.check_package(path)

    def test_package_rejects_recovery_incompatible_compression(self):
        from test_alpha import alpha,package
        import zipfile
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'rom.zip';package(path)
            with zipfile.ZipFile(path,'a') as archive:
                archive.writestr('extra.txt','unsupported',compress_type=zipfile.ZIP_BZIP2)
            with self.assertRaisesRegex(ValueError,'compression ZIP format'):alpha.check_package(path)
