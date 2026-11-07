import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from integration.samloader import metadata
from integration.firmware_check import inspect
from test_partition_profiles import s10

ROOT=Path(__file__).resolve().parents[1]
PROFILE=json.loads((ROOT/'integration/donors/s24fe.json').read_text())
AP=PROFILE['reference_ap']


def donor_fixture(root):
    s10(root)
    marker=json.loads((root/'BEYOUD-WORKSPACE.json').read_text());marker['donor_profile']=PROFILE
    (root/'BEYOUD-WORKSPACE.json').write_text(json.dumps(marker))
    config=root/'out/config.sh'
    config.write_text(config.read_text().replace('SM-S926B','SM-S721B').replace('SOURCE_HAS_SYSTEM_EXT="true"','SOURCE_HAS_SYSTEM_EXT="false"'))
    lock=root/'out/firmware-lock.json';data=json.loads(lock.read_text())
    for r in data['firmwares']:
        if r['model']=='SM-S926B':r['model']='SM-S721B';r['version']=f'{AP}/CSC/CP/{AP}'
    lock.write_text(json.dumps(data))
    base=root/'out/fw/SM-S721B_EUX'
    (root/'out/fw/SM-S926B_EUX').rename(base)
    (base/'.extracted').write_text(f'{AP}/CSC/CP/{AP}')
    (base/'system_ext').rmdir()
    (base/'system/system/build.prop').write_text('ro.build.product=r12s\nro.build.version.sdk=37\n')


class S24FEDonorTests(unittest.TestCase):
    def test_adapter_uses_r12s_not_inherited_s926b_flags(self):
        command='SRC_DIR="$1"; source "$1/integration/artisan/essi_64.sh"; printf "%s|%s|%s|%s|%s|%s" "$SOURCE_FIRMWARE" "$SOURCE_CODENAME" "$SOURCE_HAS_SYSTEM_EXT" "$SOURCE_NFC_CHIP_VENDOR" "$SOURCE_HAS_QHD_DISPLAY" "${SOURCE_USE_NATIVE_DISPLAY_STACK-unset}"'
        r=subprocess.run(['bash','-c',command,'test',str(ROOT)],capture_output=True,text=True,check=True)
        self.assertEqual(r.stdout,f'SM-S721B/EUX/{AP}|r12s|false|SLSI|false|unset')

    def test_s24fe_actual_properties_match_candidate_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);donor_fixture(root)
            result=inspect(root)
            self.assertEqual(result['firmwares'][0]['model'],'SM-S721B')
            self.assertEqual(result['firmwares'][1]['model'],'SM-G973F')

    def test_sdk_mismatch_is_not_hidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);donor_fixture(root)
            (root/'out/fw/SM-S721B_EUX/system/system/build.prop').write_text('ro.build.version.sdk=36\n')
            with self.assertRaisesRegex(ValueError,'actual SDK=36'):inspect(root)

    def test_unexpected_system_ext_needs_explicit_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);donor_fixture(root)
            (root/'out/fw/SM-S721B_EUX/system_ext').mkdir()
            with self.assertRaisesRegex(ValueError,'Unexpected source system_ext'):inspect(root)

    def test_previous_donor_cannot_be_used_with_new_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);s10(root)
            marker=json.loads((root/'BEYOUD-WORKSPACE.json').read_text());marker['donor_profile']=PROFILE
            (root/'BEYOUD-WORKSPACE.json').write_text(json.dumps(marker))
            with self.assertRaisesRegex(ValueError,'selected donor model'):inspect(root)

    def test_probe_rejects_different_ap_without_leaving_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);donor_fixture(root)
            def probe(argv,**kwargs):return subprocess.CompletedProcess([],0,f'BEYOUD_FIRMWARE\t{argv[1]}\t{argv[2]}\tOTHER/CSC/CP/OTHER\t100\n','')
            with patch.object(metadata.subprocess,'run',side_effect=probe),contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError,'differs from reference'):metadata.resolve(root)
            self.assertFalse((root/'out/firmware-lock.json').exists())

    def test_probe_locks_s24fe_and_target_without_changing_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);donor_fixture(root)
            calls=[]
            def probe(argv,**kwargs):
                calls.append(argv[1:]);version=f'{AP}/CSC/CP/{AP}' if argv[1]=='SM-S721B' else 'AP/CSC/CP/AP'
                return subprocess.CompletedProcess([],0,f'BEYOUD_FIRMWARE\t{argv[1]}\t{argv[2]}\t{version}\t100\n','')
            with patch.object(metadata.subprocess,'run',side_effect=probe),patch.object(metadata.shutil,'disk_usage') as disk,contextlib.redirect_stdout(io.StringIO()):
                disk.return_value.free=100*1024**3;metadata.resolve(root)
            self.assertEqual(calls,[['SM-S721B','EUX'],['SM-G973F','AUT']])
            self.assertEqual(metadata.get(root/'out/firmware-lock.json','SM-S721B','EUX')['version'].split('/')[0],AP)
