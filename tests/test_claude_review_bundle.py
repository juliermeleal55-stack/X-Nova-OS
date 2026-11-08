from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from scripts.create_claude_review_bundle import extract, pages


class ReviewBundleTests(unittest.TestCase):
    def test_extracts_logs_as_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);archive=root/'original.zip'
            with zipfile.ZipFile(archive,'w') as z:z.writestr('logs/failed.log','patch does not apply\n')
            extract(archive,root/'unpacked')
            self.assertEqual((root/'unpacked/logs/failed.log').read_text(),'patch does not apply\n')

    def test_rejects_path_escape_and_symlink(self):
        for name in ('../outside','/absolute','bad\\windows'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);archive=root/'original.zip'
                with zipfile.ZipFile(archive,'w') as z:z.writestr(name,'data')
                with self.assertRaises(ValueError):extract(archive,root/'unpacked')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);archive=root/'original.zip'
            with zipfile.ZipFile(archive,'w') as z:
                item=zipfile.ZipInfo('link');item.create_system=3;item.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(item,'../../outside')
            with self.assertRaises(ValueError):extract(archive,root/'unpacked')

    def test_pagination_keeps_all_annotations(self):
        with patch('scripts.create_claude_review_bundle.api',side_effect=[list(range(100)),[100]]) as api:
            self.assertEqual(pages('resource'),list(range(101)))
            self.assertEqual(api.call_args_list[1].args[0],'resource?per_page=100&page=2')
