import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from integration.onerom_port import (
    UPSTREAM_COMMIT,
    UPSTREAM_REPOSITORY,
    merge_verified_tree,
)

ROOT = Path(__file__).resolve().parents[1]


def blob_entry(relative, content, local_path=None):
    digest = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
    return {
        "upstream_path": relative,
        "source_blob_sha1": digest,
        "size_bytes": len(content),
        "local_path": local_path or "reference/onerom-port-candidates/source-snapshot/" + relative,
    }


class OneROMWorkspacePortTests(unittest.TestCase):
    def fixture(self, root):
        source = root / "upstream"
        contents = {
            "target/beyond1lte/config.sh": b'TARGET_ASSERT_MODEL=("SM-G973F" "SM-G973N")\n',
            "target/beyond1lte/postinstall.edify": b"# OneROM resize recipe\n",
            "target/beyond1lte/patches/sample/module.prop": b"id=sample\n",
            "target/beyond1lte/patches/sample/disable": b"",
            "platform/exynos9820/patches/addon/module.prop": b"id=addon\n",
        }
        rows = []
        for relative, content in contents.items():
            path = source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            rows.append(blob_entry(relative, content))
        manifest = {
            "repository": UPSTREAM_REPOSITORY,
            "commit": UPSTREAM_COMMIT,
            "license": "GPL-3.0-or-later; preserve notices",
            "retained_text_files": rows,
            "excluded_nontext_files": [],
        }
        manifest_path = root / "source-manifest.json"
        manifest_path.write_text(json.dumps(manifest))
        workspace = root / "workspace"
        (workspace / "target/beyond1lte/patches/sample").mkdir(parents=True)
        (workspace / "target/beyond1lte/config.sh").write_bytes(b"Artisan S10 config\n")
        (workspace / "target/beyond1lte/postinstall.edify").write_bytes(b"Artisan installer recipe\n")
        (workspace / "target/beyond1lte/patches/sample/module.prop").write_bytes(b"Artisan module\n")
        (workspace / "platform/exynos9820/patches/addon").mkdir(parents=True)
        (workspace / "platform/exynos9820/patches/addon/module.prop").write_bytes(contents[
            "platform/exynos9820/patches/addon/module.prop"])
        return source, manifest, manifest_path, workspace, contents

    def test_complete_tree_merges_files_and_preserves_artisan_and_installer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, manifest, manifest_path, workspace, contents = self.fixture(root)
            receipt = merge_verified_tree(
                workspace, source, manifest, manifest_path=manifest_path, repo_root=ROOT)

            self.assertEqual(receipt["source_files_verified"], 5)
            self.assertEqual(receipt["new_files"], 1)
            self.assertEqual(receipt["new_paths"], ["target/beyond1lte/patches/sample/disable"])
            self.assertEqual(receipt["overwritten_artisan_files"], 2)
            self.assertEqual(receipt["overwritten_artisan_paths"], [
                "target/beyond1lte/config.sh",
                "target/beyond1lte/patches/sample/module.prop",
            ])
            self.assertEqual(receipt["identical_artisan_files"], 1)
            self.assertEqual(receipt["identical_artisan_paths"], [
                "platform/exynos9820/patches/addon/module.prop",
            ])
            self.assertEqual(receipt["protected_from_active_installer"],
                             ["target/beyond1lte/postinstall.edify"])
            self.assertIn("target/beyond1lte/patches/sample", receipt["upstream_disabled_modules"])
            self.assertEqual(
                (workspace / "target/beyond1lte/patches/sample/module.prop").read_bytes(),
                contents["target/beyond1lte/patches/sample/module.prop"])
            self.assertEqual(
                (workspace / "target/beyond1lte/config.sh").read_bytes(),
                contents["target/beyond1lte/config.sh"])
            self.assertEqual(
                (workspace / "target/beyond1lte/postinstall.edify").read_bytes(),
                b"Artisan installer recipe\n")
            self.assertEqual(
                (workspace / "reference/onerom-upstream/target/beyond1lte/postinstall.edify").read_bytes(),
                contents["target/beyond1lte/postinstall.edify"])
            self.assertEqual(
                (workspace / "reference/onerom-upstream/target/beyond1lte/config.sh").read_bytes(),
                contents["target/beyond1lte/config.sh"])
            self.assertEqual(
                (workspace / "reference/artisan-before-onerom/target/beyond1lte/config.sh").read_bytes(),
                b"Artisan S10 config\n")
            self.assertEqual(receipt["active_installer"], "Artisan")
            self.assertFalse(receipt["one_rom_postinstall_active"])
            self.assertFalse(receipt["recovery_modified"])
            self.assertTrue((workspace / "reference/onerom-upstream/LICENSE").is_file())
            self.assertTrue((workspace / "reference/onerom-upstream/CREDITS.md").is_file())

    def test_bad_blob_and_unsafe_path_fail_before_workspace_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, manifest, manifest_path, workspace, _contents = self.fixture(root)
            before = (workspace / "target/beyond1lte/config.sh").read_bytes()
            manifest["retained_text_files"][0]["source_blob_sha1"] = "0" * 40
            with self.assertRaisesRegex(ValueError, "blob differs"):
                merge_verified_tree(
                    workspace, source, manifest, manifest_path=manifest_path, repo_root=ROOT)
            self.assertEqual((workspace / "target/beyond1lte/config.sh").read_bytes(), before)
            manifest["retained_text_files"][0]["upstream_path"] = "target/beyond1lte/../../escape"
            with self.assertRaisesRegex(ValueError, "Unsafe OneROM source path"):
                merge_verified_tree(
                    workspace, source, manifest, manifest_path=manifest_path, repo_root=ROOT)
            self.assertEqual((workspace / "target/beyond1lte/config.sh").read_bytes(), before)

    def test_destination_collision_refuses_a_second_import_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, manifest, manifest_path, workspace, _contents = self.fixture(root)
            merge_verified_tree(workspace, source, manifest, manifest_path=manifest_path, repo_root=ROOT)
            before = (workspace / "target/beyond1lte/config.sh").read_bytes()
            with self.assertRaisesRegex(ValueError, "Refusing to overwrite existing OneROM provenance"):
                merge_verified_tree(workspace, source, manifest, manifest_path=manifest_path, repo_root=ROOT)
            self.assertEqual((workspace / "target/beyond1lte/config.sh").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
