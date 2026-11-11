import json
from pathlib import Path
import unittest

from integration.targets import DEFAULT_TARGET
from scripts.verify_onerom_port import verify

ROOT = Path(__file__).resolve().parents[1]


class OneROMPortAuditTests(unittest.TestCase):
    def test_full_pinned_source_inventory_and_review_boundaries_verify(self):
        self.assertEqual(verify(), 286)

    def test_workspace_default_is_normal_s10_and_source_scope_is_explicit(self):
        self.assertEqual(DEFAULT_TARGET, 'beyond1lte')
        manifest = json.loads((ROOT / 'manifests/onerom-source-snapshot.json').read_text())
        self.assertEqual(manifest['scope'], ['target/beyond1lte/', 'platform/exynos9820/'])
        self.assertEqual(manifest['workspace_import']['active_installer'], 'Artisan')
        self.assertFalse(manifest['workspace_import']['recovery_modified'])


if __name__ == '__main__':
    unittest.main()
