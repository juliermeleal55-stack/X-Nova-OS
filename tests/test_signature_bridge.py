import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from integration.signature_bridge import allow_method, allowed, certificate, configure, verify, ARG, OWNER, MARKER, ROOT
from integration.semantic_smali import method_return


def fixture(root):
    base=root/'smali_classes8/com/android/server/pm';base.mkdir(parents=True)
    methods=(ROOT/'platform_signature_methods.smali').read_text()
    scan=base/'ScanPackageUtils.smali'
    scan.write_text('.class public '+OWNER+'\n.super Ljava/lang/Object;\n'+allow_method()+'\n'+methods+f'\n.method public static applyPolicy({ARG}ILcom/android/server/pm/pkg/AndroidPackage;Z)V\n.locals 3\ninvoke-static {{p0}}, {OWNER}->isSignedWithCustomPlatformKey({ARG})Z\nreturn-void\n.end method\n')
    install=base/'InstallPackageHelper.smali';install.write_text('.class public Lcom/android/server/pm/InstallPackageHelper;\n.super Ljava/lang/Object;\n'+f'invoke-static {{v0,v1}}, {OWNER}->setCustomSignatures({ARG}Lcom/android/server/pm/pkg/AndroidPackage;)V\n'*2)
    return scan,install


def make_cert(root,name='test'):
    pem=root/(name+'.pem')
    subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(root/(name+'.key')),'-out',str(pem),'-subj','/CN=XNova test only','-days','1'],check=True,capture_output=True)
    return pem


class SignatureBridgeTests(unittest.TestCase):
    def test_exact_package_and_path_not_prefix_or_data_update(self):
        self.assertTrue(allowed('com.android.settings','/system/priv-app/SecSettings/SecSettings.apk'))
        self.assertTrue(allowed('com.android.settings','/system/priv-app/SecSettings'))
        for package,path in [('evil.package','/system/priv-app/SecSettings/SecSettings.apk'),('com.android.settings','/data/app/SecSettings/SecSettings.apk'),('com.android.settings','/system/evil.apk'),('com.android.settings','/system/priv-app/SecSettingsFake'),('com.android.settings','/system/priv-app/SecSettings/../Other.apk')]:
            self.assertFalse(allowed(package,path))
        self.assertIn('goto/32 :denied',allow_method())

    def test_configure_validates_callers_and_replaces_actual_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);scan,install=fixture(root);pem=make_cert(root);receipt=root/'receipt.json'
            record=configure(root,pem,receipt)
            self.assertEqual(record['status'],'configured');self.assertNotIn(MARKER,scan.read_text())
            self.assertIn(certificate(pem)[0],scan.read_text());verify(root,pem,receipt)
            install.write_text(install.read_text().replace('invoke-static','invoke-virtual',1))
            with self.assertRaises(ValueError):verify(root,pem,receipt)

    def test_missing_marker_or_changed_policy_fails_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);scan,_=fixture(root);pem=make_cert(root);receipt=root/'receipt.json'
            scan.write_text(scan.read_text().replace('/system/priv-app/SecSettings/SecSettings.apk','/data/evil.apk'))
            before=scan.read_bytes()
            with self.assertRaises(ValueError):configure(root,pem,receipt)
            self.assertEqual(scan.read_bytes(),before);self.assertFalse(receipt.exists())
            scan.write_text(scan.read_text().replace(MARKER,'PUT SIGNATURE HERE'))
            with self.assertRaises(ValueError):configure(root,pem,receipt)

    def test_wrong_certificate_cannot_reuse_success_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root);pem=make_cert(root);receipt=root/'receipt.json';configure(root,pem,receipt)
            other=make_cert(root,'other')
            with self.assertRaises(ValueError):verify(root,other,receipt)

    def test_false_method_equivalent_keeps_signature_and_other_methods(self):
        text='.method public static gate(Ljava/lang/String;)Z\n.locals 3\nconst/4 v0, 0x1\nreturn v0\n.end method\n.method public keep()V\n.locals 0\nreturn-void\n.end method\n'
        result=method_return(text,'gate(Ljava/lang/String;)Z','false',True)
        self.assertIn('const/4 v0, 0x0',result);self.assertIn('keep()V',result)
        with self.assertRaises(ValueError):method_return(text,'gate(Ljava/lang/String;)Z','false',False)

    def test_preferred_signature_never_tries_broad_legacy_even_if_it_would_fit(self):
        from unittest.mock import patch
        from integration.smali_patch import apply
        key='unica/patches/signature/0001-Allow-custom-platform-signature.patch'
        with tempfile.TemporaryDirectory() as tmp:
            workspace=Path(tmp);legacy=workspace/key;legacy.parent.mkdir(parents=True)
            shutil.copyfile(ROOT.parent/'reference/boot-patch-audit/artisan'/key,legacy)
            replacement=(ROOT/'rebased-patches/0001-Scoped-platform-signature.patch').read_text()
            rejected=subprocess.CompletedProcess(['git','apply'],1,'','rejected')
            with patch('integration.smali_patch.apply_text',return_value=(rejected,[])) as attempt:
                self.assertNotEqual(apply(workspace,workspace/'decoded',legacy)[0].returncode,0)
                attempt.assert_called_once_with(workspace,workspace/'decoded',replacement)

    def test_preferred_signature_rejects_changed_original_before_application(self):
        from unittest.mock import patch
        from integration.smali_patch import apply
        key='unica/patches/signature/0001-Allow-custom-platform-signature.patch'
        with tempfile.TemporaryDirectory() as tmp:
            workspace=Path(tmp);legacy=workspace/key;legacy.parent.mkdir(parents=True)
            legacy.write_bytes((ROOT.parent/'reference/boot-patch-audit/artisan'/key).read_bytes()+b'\n')
            with patch('integration.smali_patch.apply_text') as attempt:
                result,_=apply(workspace,workspace/'decoded',legacy)
                self.assertNotEqual(result.returncode,0);attempt.assert_not_called()
                self.assertIn('hash changed',result.stderr)

    def test_apk_signing_guard_stops_before_signapk_with_invalid_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace=Path(tmp);tools=workspace/'integration';tools.mkdir()
            for name in ['signature_bridge.py','signature_policy.json','platform_signature_methods.smali','smali_paths.py']:
                shutil.copyfile(ROOT/name,tools/name)
            decoded=workspace/'apktool/system/framework/services.jar';decoded.mkdir(parents=True);fixture(decoded)
            security=workspace/'security';security.mkdir();pem=make_cert(security,'aosp_platform.x509')
            receipt=workspace/'out/beyoud-logs/platform-signature.json';configure(decoded,pem,receipt)
            receipt.write_text('{}')
            overlay=(ROOT/'artisan/apktool.sh').read_text()
            begin=overlay.index('    if [[ "$INPUT_FILE" == *".apk" ]]; then',overlay.index('BUILD()'))
            end=overlay.index('\n    mkdir -p "$(dirname "$INPUT_FILE")"',begin)
            harness='LOG() { :; }; EVAL() { echo SIGNING_REACHED; }; ROM_IS_OFFICIAL=false; INPUT_FILE=fixture.apk; SRC_DIR="$1"; APKTOOL_DIR="$1/apktool";\n'
            result=subprocess.run(['bash','-c',harness+'guard() {\n'+overlay[begin:end]+'\n}; guard','test',str(workspace)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertNotIn('SIGNING_REACHED',result.stdout)
            self.assertIn('receipt',result.stderr.lower())
