from pathlib import Path
import shutil
import tempfile
import unittest
from integration.smali_patch import apply

ROOT=Path(__file__).resolve().parents[1]
NAME='unica/mods/settings/smali/system/framework/framework.jar/0002-Introduce-SamsungPropsHooks.patch'


def setup(root):
    decoded=root/'decoded';(decoded/'smali/p').mkdir(parents=True)
    (decoded/'smali/p/Existing.smali').write_text('.class public Lp/Existing;\n.super Ljava/lang/Object;\nold\n')
    return decoded


def addition(path='smali_classes6/p/New.smali',descriptor='Lp/New;'):
    return f'diff --git a/{path} b/{path}\nnew file mode 100644\n--- /dev/null\n+++ b/{path}\n@@ -0,0 +1,2 @@\n+.class public {descriptor}\n+.super Ljava/lang/Object;\n'


class NewSmaliClassesTests(unittest.TestCase):
    def test_real_upstream_settings_props_hooks_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);decoded=setup(root);p=root/NAME;p.parent.mkdir(parents=True)
            shutil.copyfile(ROOT/'reference/patch-failure-review'/NAME,p)
            r,targets=apply(root,decoded,p)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(len(targets),1)
            self.assertIn('Lio/mesalabs/unica/SamsungPropsHooks;',targets[0].read_text())
            self.assertEqual(targets[0].relative_to(decoded).parts[0],'smali_classes2')
            self.assertIn('old',(decoded/'smali/p/Existing.smali').read_text())

    def test_existing_requested_dex_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);decoded=setup(root);(decoded/'smali_classes6').mkdir()
            p=root/'p.patch';p.write_text(addition());r,targets=apply(root,decoded,p)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertTrue((decoded/'smali_classes6/p/New.smali').is_file())

    def test_existing_class_in_other_dex_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);decoded=setup(root)
            original=decoded/'smali/p/New.smali';original.write_text('.class public Lp/New;\n.super Ljava/lang/Object;\n')
            before=original.read_bytes();p=root/'p.patch';p.write_text(addition())
            r,_=apply(root,decoded,p);self.assertNotEqual(r.returncode,0)
            self.assertEqual(original.read_bytes(),before)

    def test_missing_existing_class_is_not_created_by_edit_patch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);decoded=setup(root);p=root/'p.patch'
            p.write_text('diff --git a/smali/p/Missing.smali b/smali/p/Missing.smali\n--- a/smali/p/Missing.smali\n+++ b/smali/p/Missing.smali\n@@ -1 +1 @@\n-old\n+new\n')
            r,_=apply(root,decoded,p);self.assertNotEqual(r.returncode,0)
            self.assertFalse((decoded/'smali/p/Missing.smali').exists())

    def test_descriptor_mismatch_and_traversal_rejected(self):
        for text in (addition(descriptor='Lwrong/New;'),addition(path='smali_classes6/../../New.smali')):
            with self.subTest(text=text),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);decoded=setup(root);p=root/'p.patch';p.write_text(text)
                r,_=apply(root,decoded,p);self.assertNotEqual(r.returncode,0)

    def test_bad_existing_hunk_leaves_new_class_and_existing_file_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);decoded=setup(root);existing=decoded/'smali/p/Existing.smali';before=existing.read_bytes()
            p=root/'p.patch';p.write_text(addition()+'diff --git a/smali/p/Existing.smali b/smali/p/Existing.smali\n--- a/smali/p/Existing.smali\n+++ b/smali/p/Existing.smali\n@@ -3 +3 @@\n-not-present\n+changed\n')
            r,_=apply(root,decoded,p);self.assertNotEqual(r.returncode,0)
            self.assertEqual(existing.read_bytes(),before)
            self.assertFalse((decoded/'smali_classes2/p/New.smali').exists())

    def test_symlink_destination_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);decoded=setup(root);outside=root/'outside';outside.mkdir()
            (decoded/'smali_classes6').symlink_to(outside,target_is_directory=True)
            p=root/'p.patch';p.write_text(addition());r,_=apply(root,decoded,p)
            self.assertNotEqual(r.returncode,0);self.assertEqual(list(outside.iterdir()),[])
