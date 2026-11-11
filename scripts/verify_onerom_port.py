#!/usr/bin/env python3
"""Verify the pinned complete OneROM S10/Exynos workspace-port inventory."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "644f0aacc49ad2410e566de8deb05e6c8211d83d"
REPOSITORY = "DaDevMikey/OneROM"
SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
SCOPE_ROOTS = ("target/beyond1lte", "platform/exynos9820")


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _safe(relative: str, label: str) -> Path:
    if (not isinstance(relative, str) or not relative or "\\" in relative
            or relative.startswith("/") or ".." in Path(relative).parts):
        raise ValueError(f"Unsafe {label} path")
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError(f"Unsafe {label} path")
    return path


def _blob(path: Path, size: int, sha1: str, label: str) -> bytes:
    if not isinstance(size, int) or size < 0 or not SHA1_RE.fullmatch(str(sha1)):
        raise ValueError(f"Invalid {label} blob metadata")
    data = path.read_bytes()
    digest = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
    if len(data) != size or digest != sha1:
        raise ValueError(f"Pinned {label} blob differs: {path}")
    return data


def verify() -> int:
    """Fail closed unless every retained text blob and all scope metadata match."""
    source = _json("manifests/onerom-source-snapshot.json")
    audit = _json("manifests/onerom.json")
    cross = _json("manifests/cross-audit.json")["sources"]["onerom"]
    candidates = _json("manifests/onerom-port-candidates.json")
    workspace = source.get("workspace_import", {})

    if (source.get("repository") != REPOSITORY or source.get("commit") != COMMIT
            or source.get("status") != "complete-upstream-inventory-workspace-port"
            or source.get("scope") != ["target/beyond1lte/", "platform/exynos9820/"]
            or len(source.get("retained_text_files", [])) != 283
            or len(source.get("excluded_nontext_files", [])) != 191
            or workspace.get("upstream_files") != 474
            or workspace.get("upstream_bytes") != 326_008_869
            or workspace.get("text_files_in_repository") != 283
            or workspace.get("nontext_files_fetched_into_workspace") != 191
            or workspace.get("active_installer") != "Artisan"
            or workspace.get("artisan_installer_replaced") is not False
            or workspace.get("recovery_modified") is not False):
        raise ValueError("OneROM S10 source inventory or workspace boundaries are incomplete")

    expected_status = (
        "283 exact text/source files plus a complete 474-blob inventory are retained in this repository; "
        "workspace preparation fetches and SHA-verifies the full target/beyond1lte and platform/exynos9820 trees, "
        "including 191 non-text assets, into the SM-G973F workspace. The adapted search-indexing candidate remains "
        "outside the build; its upstream module disable marker is preserved. OneROM postinstall.edify remains "
        "reference-only and the Artisan installer stays active."
    )
    if (audit.get("repository") != REPOSITORY or audit.get("commit") != COMMIT
            or not audit.get("license", "").startswith("GPL-3.0-or-later")
            or audit.get("local_reference_status") != expected_status):
        raise ValueError("OneROM audit manifest is missing complete-port provenance")
    if (cross.get("commit") != COMMIT or cross.get("inventory_truncated") is not False
            or cross.get("files") != 4_468
            or cross.get("local_reference_status") != (
                "Complete pinned inventory in manifests/onerom-source-snapshot.json; repository retains 283 "
                "byte-exact text/source files, and beyond1lte workspace preparation imports and verifies all 474 "
                "target/platform blobs, including binary assets. OneROM postinstall.edify remains reference-only; "
                "Artisan installer and recovery are not replaced or modified.")):
        raise ValueError("OneROM cross-audit does not describe the complete S10 workspace port")

    retained = source["retained_text_files"]
    excluded = source["excluded_nontext_files"]
    seen: set[str] = set()
    scope_totals = {root: {"text_count": 0, "text_bytes": 0,
                           "binary_count": 0, "binary_bytes": 0} for root in SCOPE_ROOTS}
    count = 0
    for entry in retained:
        upstream = entry.get("upstream_path")
        if (not isinstance(upstream, str)
                or not any(upstream.startswith(root + "/") for root in SCOPE_ROOTS)
                or upstream in seen):
            raise ValueError(f"Duplicate or out-of-scope OneROM path: {upstream}")
        seen.add(upstream)
        local_path = entry.get("local_path")
        expected_local = "reference/onerom-port-candidates/source-snapshot/" + upstream
        if local_path != expected_local:
            raise ValueError(f"Unexpected retained OneROM source destination: {upstream}")
        path = _safe(local_path, "retained OneROM text source")
        data = _blob(path, entry.get("size_bytes"), entry.get("source_blob_sha1"), "OneROM source")
        if hashlib.sha256(data).hexdigest() != entry.get("sha256"):
            raise ValueError(f"OneROM source SHA-256 differs: {path}")
        root = next(item for item in SCOPE_ROOTS if upstream.startswith(item + "/"))
        scope_totals[root]["text_count"] += 1
        scope_totals[root]["text_bytes"] += len(data)
        count += 1

    for entry in excluded:
        upstream = entry.get("upstream_path")
        if (not isinstance(upstream, str)
                or not any(upstream.startswith(root + "/") for root in SCOPE_ROOTS)
                or upstream in seen or not entry.get("reason")):
            raise ValueError(f"Duplicate or invalid OneROM non-text path: {upstream}")
        seen.add(upstream)
        if not SHA1_RE.fullmatch(str(entry.get("source_blob_sha1", ""))) \
                or not isinstance(entry.get("size_bytes"), int) or entry["size_bytes"] < 0:
            raise ValueError(f"Invalid OneROM non-text metadata: {upstream}")
        relative_binary = "reference/onerom-port-candidates/source-snapshot/" + upstream
        path = _safe(relative_binary, "metadata-only OneROM binary")
        lexical_path = ROOT / relative_binary
        if lexical_path.exists() or lexical_path.is_symlink():
            raise ValueError(f"OneROM binary unexpectedly retained in Git snapshot: {lexical_path}")
        root = next(item for item in SCOPE_ROOTS if upstream.startswith(item + "/"))
        scope_totals[root]["binary_count"] += 1
        scope_totals[root]["binary_bytes"] += entry["size_bytes"]

    expected_totals = {
        "target/beyond1lte": {"text_count": 224, "text_bytes": 897_334,
                               "binary_count": 9, "binary_bytes": 141_827_295},
        "platform/exynos9820": {"text_count": 59, "text_bytes": 428_502,
                                 "binary_count": 182, "binary_bytes": 182_855_738},
    }
    if scope_totals != expected_totals or len(seen) != 474:
        raise ValueError("OneROM tree counts or byte totals changed")

    if (candidates.get("repository") != REPOSITORY
            or candidates.get("audited_commit") != COMMIT
            or candidates.get("status") != "complete-upstream-tree-workspace-port; adapted-search-indexing-candidate-review-only"
            or candidates.get("session_date") != "2026-10-30"
            or len(candidates.get("candidates", [])) != 1):
        raise ValueError("OneROM candidate manifest is incomplete")
    policy = candidates.get("candidate_policy", {})
    for key, value in {
        "build_enabled": False,
        "workspace_preparation_copies_candidate": False,
        "complete_upstream_tree_workspace_import": True,
        "upstream_search_indexing_module_copied": True,
        "upstream_search_indexing_disable_marker_preserved": True,
        "adapted_candidate_copied_or_wired": False,
        "one_rom_postinstall_active": False,
        "artisan_installer_replaced": False,
        "recovery_modified": False,
    }.items():
        if policy.get(key) is not value:
            raise ValueError(f"OneROM candidate policy changed: {key}")

    license_entry = next((item for item in audit.get("files", []) if item.get("path") == "LICENSE"), None)
    patch_entry = next((item for item in audit.get("files", [])
                        if item.get("path", "").endswith(
                            "search_indexing/smali/system/priv-app/SecSettingsIntelligence/"
                            "SecSettingsIntelligence.apk/0001-Skip-absent-policy-resource-IDs.patch")), None)
    if license_entry is None or patch_entry is None:
        raise ValueError("OneROM license or review candidate lacks upstream blob metadata")
    _blob(_safe("reference/onerom-port-candidates/LICENSE", "OneROM license"),
          license_entry["size"], license_entry["sha"], "OneROM license")
    count += 1

    candidate = candidates["candidates"][0]
    if (candidate.get("id") != "beyond1lte-search-indexing"
            or candidate.get("source_blob_sha1") != patch_entry["sha"]
            or candidate.get("source_size_bytes") != patch_entry["size"]
            or candidate.get("source_sha256") != candidate.get("local_sha256")
            or candidate.get("status") != "review-only-unvalidated-donor"
            or candidate.get("build_integration") is not False
            or not candidate.get("upstream_module_credit")
            or not candidate.get("upstream_commit_author_integrator")):
        raise ValueError("OneROM search-indexing review policy changed")
    patch_path = _safe(candidate.get("local_path", ""), "OneROM review patch")
    if not patch_path.is_relative_to((ROOT / "reference/onerom-port-candidates").resolve()):
        raise ValueError("OneROM review patch escaped its provenance directory")
    data = _blob(patch_path, patch_entry["size"], patch_entry["sha"], "OneROM search-indexing patch")
    if hashlib.sha256(data).hexdigest() != candidate.get("local_sha256"):
        raise ValueError("OneROM review patch SHA-256 differs")
    count += 1

    adapter_path = _safe(candidate.get("adapter_path", ""), "OneROM review adapter")
    if (not adapter_path.is_relative_to((ROOT / "reference/onerom-port-candidates").resolve())
            or not adapter_path.is_file()
            or hashlib.sha256(adapter_path.read_bytes()).hexdigest() != candidate.get("adapter_sha256")):
        raise ValueError("OneROM review adapter is missing or modified")
    count += 1

    prepare = (ROOT / "scripts/prepare_workspace.py").read_text(encoding="utf-8")
    if ("import_onerom_sources(workspace, codename)" not in prepare
            or "install_s10_compat(workspace, codename)" not in prepare):
        raise ValueError("Complete OneROM import is not wired into S10 workspace preparation")
    return count


if __name__ == "__main__":
    print(f"{verify()} OneROM source and provenance files verified")
