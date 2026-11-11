import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ROOT = ROOT / 'reference/onerom-port-candidates'
PATCH = CANDIDATE_ROOT / 'search_indexing/0001-Skip-absent-policy-resource-IDs.patch'
ADAPTER_PATH = CANDIDATE_ROOT / 'search_indexing/adapt_candidate.py'
MANIFEST = ROOT / 'manifests/onerom-port-candidates.json'
sys.path.insert(0, str(ADAPTER_PATH.parent))
from adapt_candidate import CandidateMismatch, adapt_text


def synthetic_smali(default='-0x1', return_type='Z'):
    return f'''\
.class public Lcom/android/settings/intelligence/search/indexing/DevicePolicyResourcesUtils;
.method public static syntheticFixture(Landroid/content/res/Resources;Landroid/content/res/TypedArray;){return_type}
    .locals 2
    const/4 v1, 0x0
    const/4 v0, {default}
    invoke-virtual {{p1, v1, v0}}, Landroid/content/res/TypedArray;->getResourceId(II)I

    move-result p1

    invoke-virtual {{p0, p1}}, Landroid/content/res/Resources;->getResourceEntryName(I)Ljava/lang/String;

    move-result-object p0
    const/4 p0, 0x1
    return p0
.end method
'''


class OneROMPortCandidateTests(unittest.TestCase):
    def test_manifest_keeps_snapshot_authorization_and_candidate_inactive(self):
        manifest = json.loads(MANIFEST.read_text())
        self.assertEqual(manifest['audited_commit'], '644f0aacc49ad2410e566de8deb05e6c8211d83d')
        self.assertEqual(manifest['session_date'], '2026-10-30')
        self.assertEqual(manifest['upstream_timing']['repository_created_at'], '2026-11-03T08:40:54Z')
        self.assertIn('user explicitly approved', manifest['upstream_timing']['note'])
        self.assertEqual(
            manifest['status'],
            'complete-upstream-tree-workspace-port; adapted-search-indexing-candidate-review-only')
        self.assertFalse(manifest['candidate_policy']['workspace_preparation_copies_candidate'])
        self.assertTrue(manifest['candidate_policy']['complete_upstream_tree_workspace_import'])
        self.assertTrue(manifest['candidate_policy']['upstream_search_indexing_module_copied'])
        self.assertTrue(manifest['candidate_policy']['upstream_search_indexing_disable_marker_preserved'])
        self.assertFalse(manifest['candidate_policy']['adapted_candidate_copied_or_wired'])
        self.assertFalse(manifest['candidate_policy']['build_enabled'])
        self.assertFalse(manifest['candidate_policy']['device_tested'])
        snapshot = json.loads((ROOT / 'manifests/onerom-source-snapshot.json').read_text())
        self.assertEqual(snapshot['status'], 'complete-upstream-inventory-workspace-port')
        self.assertEqual(snapshot['workspace_import']['upstream_files'], 474)
        self.assertEqual(snapshot['workspace_import']['upstream_bytes'], 326008869)
        self.assertFalse(snapshot['workspace_import']['recovery_modified'])
        self.assertEqual(len(manifest['candidates']), 1)
        candidate = manifest['candidates'][0]
        self.assertEqual(candidate['status'], 'review-only-unvalidated-donor')
        self.assertFalse(candidate['build_integration'])
        self.assertEqual(candidate['upstream_module_credit'], 'UN1CA contributors')
        self.assertEqual(candidate['upstream_commit_author_integrator'], 'DaManMikey')
        self.assertEqual(candidate['adapter_path'],
                         'reference/onerom-port-candidates/search_indexing/adapt_candidate.py')
        self.assertEqual(hashlib.sha256(ADAPTER_PATH.read_bytes()).hexdigest(),
                         candidate['adapter_sha256'])

    def test_retained_patch_and_gpl_license_match_pinned_upstream_blobs(self):
        data = PATCH.read_bytes()
        blob = b'blob ' + str(len(data)).encode() + b'\0' + data
        self.assertEqual(hashlib.sha1(blob).hexdigest(), '7add52275f17c126d019029809fcd82d13a073a1')
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         'bfa847f8333636019773d46d203b35b65c94fd3a8acdfa916c9e292af3534081')
        license_text = (CANDIDATE_ROOT / 'LICENSE').read_text()
        self.assertIn('GNU GENERAL PUBLIC LICENSE', license_text)
        self.assertIn('Version 3, 29 June 2007', license_text)
        license_data = (CANDIDATE_ROOT / 'LICENSE').read_bytes()
        license_blob = b'blob ' + str(len(license_data)).encode() + b'\0' + license_data
        self.assertEqual(hashlib.sha1(license_blob).hexdigest(), '94a9ed024d3859793618152ea559a168bbcbb5e2')
        readme = (PATCH.parent / 'README.md').read_text()
        for credit in ('DaManMikey', 'UN1CA contributors', 'GPL-3.0-or-later',
                       'not integrated', '2026-11-05', 'adapt_candidate.py'):
            self.assertIn(credit, readme)

    def test_candidate_and_adapter_are_outside_every_build_input_tree(self):
        self.assertTrue(PATCH.resolve().is_relative_to((ROOT / 'reference').resolve()))
        self.assertTrue(ADAPTER_PATH.resolve().is_relative_to((ROOT / 'reference').resolve()))
        self.assertFalse((ROOT / 'target/beyond1lte/patches/search_indexing').exists())
        self.assertFalse((ROOT / 'platform/exynos9820/patches/search_indexing').exists())
        for name in ('scripts/prepare_workspace.py', 'integration/s10_compat.py'):
            self.assertNotIn('onerom-port-candidates', (ROOT / name).read_text())
        self.assertNotIn('search_indexing/0001-Skip-absent-policy-resource-IDs.patch',
                         (ROOT / 'scripts/prepare_workspace.py').read_text())

    def test_adapter_adapts_only_the_proven_sentinel_and_preserves_valid_lookup(self):
        original = synthetic_smali()
        adapted = adapt_text(original)
        self.assertIn('if-ne p1, v0, :xnova_s10_policy_resource_present', adapted)
        self.assertIn('const/4 v0, 0x0\n    return v0', adapted)
        self.assertIn(':xnova_s10_policy_resource_present\n\n    invoke-virtual {p0, p1}', adapted)
        self.assertIn('getResourceEntryName(I)Ljava/lang/String;', adapted)
        self.assertEqual(adapted.count('getResourceEntryName(I)'), 1)
        self.assertLess(adapted.index('move-result p1'), adapted.index('if-ne p1, v0'))

    def test_adapter_refuses_unproven_or_ambiguous_inputs(self):
        with self.assertRaises(CandidateMismatch):
            adapt_text(synthetic_smali(default='0x0'))
        with self.assertRaises(CandidateMismatch):
            adapt_text(synthetic_smali(return_type='Ljava/lang/String;'))
        with self.assertRaises(CandidateMismatch):
            adapt_text(synthetic_smali().replace(
                'invoke-virtual {p1, v1, v0}, Landroid/content/res/TypedArray;->getResourceId(II)I',
                'invoke-virtual/range {p1 .. v0}, Landroid/content/res/TypedArray;->getResourceId(II)I'))
        with self.assertRaises(CandidateMismatch):
            adapt_text(synthetic_smali().replace(
                'const/4 v0, -0x1', 'const/4 v0, -0x1\n    const/4 v0, 0x0'))

    def test_adapter_cli_writes_new_output_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / 'source.smali'
            output = workspace / 'candidate.smali'
            original = synthetic_smali()
            source.write_text(original)
            result = subprocess.run([sys.executable, str(ADAPTER_PATH), str(source), str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(source.read_text(), original)
            self.assertIn(':xnova_s10_policy_resource_present', output.read_text())
            output_before = output.read_bytes()
            result = subprocess.run([sys.executable, str(ADAPTER_PATH), str(source), str(output)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), output_before)
            self.assertEqual(source.read_text(), original)

    def test_upstream_patch_applies_only_to_a_synthetic_smali_context(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / (
                'smali/com/android/settings/intelligence/search/indexing/'
                'DevicePolicyResourcesUtils.smali'
            )
            target.parent.mkdir(parents=True)
            target.write_text(synthetic_smali())
            subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=workspace,
                           check=True, capture_output=True, text=True)
            subprocess.run(['git', 'apply', str(PATCH)], cwd=workspace,
                           check=True, capture_output=True, text=True)
            result = target.read_text()
            self.assertLess(result.index('move-result p1'), result.index('if-ne p1, v0'))
            self.assertLess(result.index('if-ne p1, v0'), result.index('getResourceEntryName'))
            self.assertIn('const/4 v0, -0x1', result)
            self.assertIn(':s10_policy_resource_present', result)
            self.assertIn('return p0', result)

    def test_source_patch_has_no_partition_or_installer_side_effects(self):
        text = PATCH.read_text()
        for forbidden in ('e2fsck', 'resize2fs', 'format(', 'block_image_update',
                          'setprop ', 'ro.product.', 'mount('):
            self.assertNotIn(forbidden, text)
        self.assertIn('Resources;->getResourceEntryName(I)Ljava/lang/String;', text)
        self.assertIn('TypedArray.getString', text)


if __name__ == '__main__':
    unittest.main()
