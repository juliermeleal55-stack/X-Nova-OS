import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from integration.smali_patch import apply
from scripts.replay_upstream_candidates import replay, fixed_boolean

ROOT=Path(__file__).resolve().parents[1]
KEY='unica/mods/settings/smali/system/framework/services.jar/0002-Allow-app-downgrade.patch'


class BootPatchAuditTests(unittest.TestCase):
    def test_downgrade_returns_true_local_not_flags_parameter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);decoded=root/'decoded';decoded.mkdir()
            target=decoded/'smali_classes9/com/android/server/pm/PackageManagerServiceUtils.smali'
            target.parent.mkdir(parents=True)
            target.write_text('.class public Lcom/android/server/pm/PackageManagerServiceUtils;\n.super Ljava/lang/Object;\n.method public static isDowngradePermitted(IZ)Z\n.locals 1\nconst/4 v0, 0x1\nreturn v1\n.end method\n')
            upstream=root/KEY;upstream.parent.mkdir(parents=True);shutil.copyfile(ROOT/'reference/boot-patch-audit/artisan'/KEY,upstream)
            result,_=apply(root,decoded,upstream)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('const/4 v0, 0x1\n\n    return v0',target.read_text())
            self.assertNotIn('return v1',target.read_text())
            stable=target.read_bytes();upstream.write_text(upstream.read_text()+'\n')
            self.assertNotEqual(apply(root,decoded,upstream)[0].returncode,0)
            self.assertEqual(target.read_bytes(),stable)

    def test_downgrade_does_not_create_absent_core_class(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);decoded=root/'decoded';decoded.mkdir()
            upstream=root/KEY;upstream.parent.mkdir(parents=True);shutil.copyfile(ROOT/'reference/boot-patch-audit/artisan'/KEY,upstream)
            self.assertNotEqual(apply(root,decoded,upstream)[0].returncode,0)
            self.assertEqual(list(decoded.rglob('*.smali')),[])

    def test_upstream_replay_reports_unavailable_not_pass_for_missing_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'patch-preflight.json').write_text(json.dumps({'events':[]}))
            result=replay(root)
            self.assertEqual(len(result['results']),15)
            self.assertTrue(all(x['status']=='unavailable' for x in result['results']))

    def test_upstream_replay_requires_exact_hash_and_checks_context(self):
        spec=dict(id='fixture',original_patch='fixture.patch',candidate='reference/boot-patch-audit/fixture.patch')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);evidence=root/'reference/boot-patch-audit';evidence.mkdir(parents=True)
            (root/'integration').mkdir();(root/'integration/boot_patch_candidates.json').write_text(json.dumps([spec]))
            source='.class public Lp/A;\n.super Ljava/lang/Object;\nold\n';digest=hashlib.sha256(source.encode()).hexdigest()
            captured=root/'artifacts';captured.mkdir();(captured/'snapshot.smali').write_text(source)
            name='decoded/smali_classes9/p/A.smali'
            report={'events':[{'kind':'patch','patch':'fixture.patch','inputs':{name:digest}}]}
            (captured/'patch-preflight.json').write_text(json.dumps(report))
            candidate=evidence/'fixture.patch'
            candidate.write_text('diff --git a/smali/p/A.smali b/smali/p/A.smali\n--- a/smali/p/A.smali\n+++ b/smali/p/A.smali\n@@ -1,3 +1,3 @@\n .class public Lp/A;\n .super Ljava/lang/Object;\n-old\n+new\n')
            with patch('scripts.replay_upstream_candidates.ROOT',root):
                self.assertEqual(replay(captured)['results'][0]['status'],'applied-to-retained-input')
                candidate.write_text(candidate.read_text().replace('-old','-different'))
                self.assertEqual(replay(captured)['results'][0]['status'],'rejected')
                (captured/'snapshot.smali').write_text(source+'# changed\n')
                self.assertEqual(replay(captured)['results'][0]['status'],'unavailable')
            self.assertEqual((captured/'snapshot.smali').read_text(),source+'# changed\n')

    def test_boolean_proof_rejects_assumed_or_overwritten_register(self):
        text='.method static constructor <clinit>()V\n.locals 4\nconst/4 v3, 0x0\nif-eqz v0, :end\n:end\nsput-boolean v3, Lp/A;->FLAG:Z\nreturn-void\n.end method\n'
        self.assertIs(fixed_boolean(text,'FLAG'),False)
        self.assertEqual(fixed_boolean(text.replace(':end\nsput',':end\nmove-result v3\nsput'),'FLAG'),'unknown')
        self.assertEqual(fixed_boolean(text.replace('const/4 v3, 0x0','const/4 v2, 0x0'),'FLAG'),'unknown')

    def test_optical_rewrite_does_not_reuse_or_overwrite_live_donor_boolean(self):
        from integration.semantic_smali import force_boolean_fields
        text='.class public Lp/A;\n.super Ljava/lang/Object;\n.field public static final OPTICAL:Z\n.method static constructor <clinit>()V\n.locals 24\nconst/4 v3, 0x1\nsput-boolean v3, Lp/A;->OPTICAL:Z\nsput-boolean v3, Lp/A;->KEEP:Z\nreturn-void\n.end method\n'
        result=force_boolean_fields(text,{'OPTICAL':False})
        self.assertIn('.locals 25',result)
        self.assertIn('const/16 v24, 0x0\n\n    sput-boolean v24, Lp/A;->OPTICAL:Z',result)
        self.assertIn('sput-boolean v3, Lp/A;->KEEP:Z',result)
        self.assertIs(fixed_boolean(result,'OPTICAL'),False)
        self.assertEqual(force_boolean_fields(result,{'OPTICAL':False}),result)
        with self.assertRaises(ValueError):force_boolean_fields(text.replace('.locals 24','.locals 256'),{'OPTICAL':False})
        with self.assertRaises(ValueError):force_boolean_fields(text,{'ABSENT':False})
        with self.assertRaises(ValueError):force_boolean_fields(text.replace('sput-boolean v3, Lp/A;->KEEP:Z','sput-boolean v3, Lp/A;->OPTICAL:Z'),{'OPTICAL':False})

    def test_guarded_optical_fix_is_pinned_and_descriptor_resolved(self):
        key='unica/patches/product_feature/fingerprint/SystemUI.apk/0001-Set-SECURITY_FINGERPRINT_IN_DISPLAY_OPTICAL-to-false.patch'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);decoded=root/'decoded';decoded.mkdir()
            target=decoded/'smali_classes9/com/android/systemui/LsRune.smali';target.parent.mkdir(parents=True)
            target.write_text('.class public Lcom/android/systemui/LsRune;\n.super Ljava/lang/Object;\n.field public static final SECURITY_FINGERPRINT_IN_DISPLAY_OPTICAL:Z\n.method static constructor <clinit>()V\n.locals 6\nconst/4 v3, 0x1\nsput-boolean v3, Lcom/android/systemui/LsRune;->SECURITY_FINGERPRINT_IN_DISPLAY_OPTICAL:Z\nreturn-void\n.end method\n')
            original=root/key;original.parent.mkdir(parents=True);shutil.copyfile(ROOT/'reference/boot-patch-audit/artisan'/key,original)
            result,_=apply(root,decoded,original)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIs(fixed_boolean(target.read_text(),'SECURITY_FINGERPRINT_IN_DISPLAY_OPTICAL'),False)
            before=target.read_bytes();original.write_text(original.read_text()+'\n')
            self.assertNotEqual(apply(root,decoded,original)[0].returncode,0)
            self.assertEqual(target.read_bytes(),before)
