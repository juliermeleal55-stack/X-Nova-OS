import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from integration.dex_entries import units, create, verify_decode, build_rows, MAP


def write_class(root, directory, name):
    p=root/directory/f'p/{name}.smali';p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(f'.class public Lp/{name};\n.super Ljava/lang/Object;\n')
    return p


class LogicalDexTests(unittest.TestCase):
    def test_logical_order_is_physical_numeric_then_internal_numeric(self):
        entries=['classes10.dex','classes2.dex','classes.dex/3','classes.dex/2','classes.dex']
        result=units(['classes2.dex','classes10.dex','classes.dex'],'\n'.join(entries))
        self.assertEqual([u['entry'] for u in result],['classes.dex','classes.dex/2','classes.dex/3','classes2.dex','classes10.dex'])
        self.assertEqual([u['output'] for u in result],['classes.dex','classes2.dex','classes3.dex','classes4.dex','classes5.dex'])
        self.assertEqual(result[1]['smali'],'smali_classes2')

    def test_missing_duplicate_or_unsafe_selectors_are_rejected(self):
        for listed in ['', 'classes.dex\nclasses.dex', 'classes.dex/2', 'classes.dex\nclasses.dex/3', 'classes.dex\nclasses.dex/01', 'classes.dex\nclasses.dex/../2', 'classes.dex\nother.dex', '/classes.dex']:
            with self.subTest(listed=listed), self.assertRaises(ValueError):units(['classes.dex'],listed)
        with self.assertRaises(ValueError):units(['classes.dex','classes2.dex'],'classes.dex')
        with self.assertRaises(ValueError):units(['classes.dex','classes.dex'],'classes.dex')

    def fixture(self,root):
        data=dict(schema_version=1,units=units(['classes.dex'],'classes.dex\nclasses.dex/2'))
        (root/MAP).write_text(json.dumps(data))
        write_class(root,'smali','A');write_class(root,'smali_classes2','B')
        return data

    def test_plan_reads_archive_and_invokes_real_list_command_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'services.jar'
            with zipfile.ZipFile(source,'w') as archive:archive.writestr('classes.dex',b'fixture')
            with patch('integration.dex_entries.command',return_value='classes.dex\nclasses.dex/2\n') as call:
                self.assertEqual(len(create(source)['units']),2)
                call.assert_called_once_with('list','dex',str(source))

    def test_inventory_requires_all_source_classes_and_unique_descriptors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root)
            def source(*args):return 'Lp/A;\n' if args[-1].endswith('classes.dex') else 'Lp/B;\n'
            with patch('integration.dex_entries.command',side_effect=source):
                verify_decode(Path('services.jar'),root)
                (root/'smali_classes2/p/B.smali').unlink()
                with self.assertRaises(ValueError):verify_decode(Path('services.jar'),root)

    def test_duplicate_class_across_logical_units_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root);(root/'smali_classes2/p/B.smali').unlink();write_class(root,'smali_classes2','A')
            with patch('integration.dex_entries.command',return_value='Lp/A;\n'):
                with self.assertRaises(ValueError):verify_decode(Path('services.jar'),root)

    def test_build_preserves_all_units_and_assigns_api_to_next_added_dex(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root)
            (root/'dex_api_versions.tsv').write_text('smali\t35\nsmali_classes2\t34\n')
            (root/'dex_class_inventory.json').write_text(json.dumps({'smali':['Lp/A;'],'smali_classes2':['Lp/B;']}))
            write_class(root,'smali_classes3','Hook')
            self.assertEqual(build_rows(root),[('smali',35,'classes.dex'),('smali_classes2',34,'classes2.dex'),('smali_classes3',35,'classes3.dex')])
            (root/'smali_classes2/p/B.smali').unlink()
            with self.assertRaises(ValueError):build_rows(root)

    def test_build_rejects_gaps_missing_metadata_duplicate_classes_and_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root)
            apis=root/'dex_api_versions.tsv';apis.write_text('smali\t35\nsmali_classes2\t34\n')
            (root/'dex_class_inventory.json').write_text(json.dumps({'smali':['Lp/A;'],'smali_classes2':['Lp/B;']}))
            new=write_class(root,'smali_classes4','Hook')
            with self.assertRaises(ValueError):build_rows(root)
            new.unlink();new.parent.rmdir();new.parent.parent.rmdir()
            apis.write_text('smali\t35\n')
            with self.assertRaises(ValueError):build_rows(root)
            apis.write_text('smali\t35\nsmali_classes2\t34\n')
            extra=write_class(root,'smali_classes2','A')
            with self.assertRaises(ValueError):build_rows(root)
            extra.unlink();extra.symlink_to(root/'smali/p/A.smali')
            with self.assertRaises(ValueError):build_rows(root)

    def test_tampered_mapping_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);data=self.fixture(root);data['units'][1]['output']='classes.dex';(root/MAP).write_text(json.dumps(data))
            with self.assertRaises(ValueError):build_rows(root)

    def test_decode_cache_requires_success_marker_not_just_directory(self):
        import shutil
        import subprocess
        from integration.preflight_policy import install
        repo=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);shutil.copytree(repo/'reference/build',root,dirs_exist_ok=True);install(root)
            raw=(root/'scripts/utils/module_utils.sh').read_text()
            function=raw[raw.index('DECODE_APK()\n'):raw.index('# DOWNLOAD_FILE')]
            cache=root/'apktool/system/framework/services.jar';cache.mkdir(parents=True)
            harness='_CHECK_NON_EMPTY_PARAM() { return 0; }; LOGE() { echo "$*" >&2; };\n'+function+'\nAPKTOOL_DIR="$1"; DECODE_APK system system/framework/services.jar\n'
            args=['bash','-c',harness,'cache-test',str(root/'apktool')]
            failed=subprocess.run(args,capture_output=True,text=True)
            self.assertNotEqual(failed.returncode,0)
            self.assertIn('Incomplete or legacy decode cache',failed.stderr)
            (cache/'.beyoud_decode_complete').touch()
            self.assertEqual(subprocess.run(args,capture_output=True).returncode,0)
