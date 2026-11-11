#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Import the complete pinned OneROM S10/Exynos source trees into a workspace."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_REPOSITORY = "DaDevMikey/OneROM"
UPSTREAM_URL = "https://github.com/DaDevMikey/OneROM.git"
UPSTREAM_COMMIT = "644f0aacc49ad2410e566de8deb05e6c8211d83d"
SCOPE_ROOTS = ("target/beyond1lte", "platform/exynos9820")
EXPECTED_COUNTS = {"target/beyond1lte": 233, "platform/exynos9820": 241}
EXPECTED_BYTES = {"target/beyond1lte": 142_724_629, "platform/exynos9820": 183_284_240}
EXPECTED_TOTAL_FILES = 474
EXPECTED_TOTAL_BYTES = 326_008_869
LICENSE_BLOB_SHA1 = "94a9ed024d3859793618152ea559a168bbcbb5e2"

# Keep the OneROM installer recipe as review material, never in the active
# Artisan installer path. Other OneROM target/platform files are merged in place.
PROTECTED_ACTIVE_PATHS = {"target/beyond1lte/postinstall.edify"}
# Keep exact upstream copies of files that the project overlay intentionally
# adapts after import, so provenance survives those project-authored changes.
UPSTREAM_SHADOW_PATHS = {
    "target/beyond1lte/config.sh",
    "target/beyond1lte/postinstall.edify",
    "platform/exynos9820/patches/miscs/customize.sh",
    "platform/exynos9820/patches/extremekrnl/customize.sh",
}


def _safe_relative(value: str) -> PurePosixPath:
    if (not isinstance(value, str) or not value or "\\" in value
            or value.startswith("/") or any(part in ("", ".", "..") for part in value.split("/"))):
        raise ValueError(f"Unsafe OneROM source path: {value!r}")
    relative = PurePosixPath(value)
    if not any(value.startswith(root + "/") for root in SCOPE_ROOTS):
        raise ValueError(f"OneROM path is outside the requested S10 trees: {value}")
    return relative


def _entries(manifest: dict, *, require_pinned_inventory: bool) -> list[dict]:
    if (manifest.get("repository") != UPSTREAM_REPOSITORY
            or manifest.get("commit") != UPSTREAM_COMMIT
            or not str(manifest.get("license", "")).startswith("GPL-3.0-or-later")):
        raise ValueError("OneROM source manifest does not match the approved repository, commit and license")

    retained = manifest.get("retained_text_files", [])
    excluded = manifest.get("excluded_nontext_files", [])
    if not isinstance(retained, list) or not isinstance(excluded, list):
        raise ValueError("Malformed OneROM source inventory")
    rows = []
    totals = {root: {"files": 0, "bytes": 0} for root in SCOPE_ROOTS}
    seen = set()
    for kind, group in (("text", retained), ("binary", excluded)):
        for entry in group:
            if not isinstance(entry, dict):
                raise ValueError("Malformed OneROM source inventory entry")
            upstream = entry.get("upstream_path")
            relative = _safe_relative(upstream)
            key = relative.as_posix()
            if key in seen:
                raise ValueError(f"Duplicate OneROM source path: {key}")
            seen.add(key)
            size = entry.get("size_bytes")
            blob_sha = entry.get("source_blob_sha1")
            if (not isinstance(size, int) or size < 0
                    or not isinstance(blob_sha, str) or len(blob_sha) != 40
                    or any(char not in "0123456789abcdef" for char in blob_sha)):
                raise ValueError(f"Invalid OneROM Git blob metadata: {key}")
            if kind == "text" and not str(entry.get("local_path", "")).startswith(
                    "reference/onerom-port-candidates/source-snapshot/"):
                raise ValueError(f"Invalid retained OneROM source path: {key}")
            if kind == "binary" and not entry.get("reason"):
                raise ValueError(f"Missing OneROM non-text inventory reason: {key}")
            scope = next(root for root in SCOPE_ROOTS if key.startswith(root + "/"))
            totals[scope]["files"] += 1
            totals[scope]["bytes"] += size
            rows.append({"upstream_path": key, "size_bytes": size,
                         "source_blob_sha1": blob_sha, "kind": kind})

    if require_pinned_inventory:
        if (manifest.get("status") != "complete-upstream-inventory-workspace-port"
                or len(retained) != 283 or len(excluded) != 191
                or len(rows) != EXPECTED_TOTAL_FILES
                or sum(row["size_bytes"] for row in rows) != EXPECTED_TOTAL_BYTES):
            raise ValueError("OneROM inventory is incomplete or differs from the pinned workspace port")
        for root in SCOPE_ROOTS:
            if totals[root] != {"files": EXPECTED_COUNTS[root], "bytes": EXPECTED_BYTES[root]}:
                raise ValueError(f"OneROM inventory totals changed for {root}")
    return sorted(rows, key=lambda row: row["upstream_path"])


def _git_blob(path: Path) -> tuple[int, str]:
    size = path.stat().st_size
    digest = hashlib.sha1()
    digest.update(b"blob " + str(size).encode("ascii") + b"\0")
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return size, digest.hexdigest()


def _source_files(source_root: Path) -> dict[str, Path]:
    found = {}
    for scope in SCOPE_ROOTS:
        base = source_root / scope
        if base.is_symlink() or not base.is_dir():
            raise ValueError(f"Missing or unsafe fetched OneROM tree: {scope}")
        for current, directories, filenames in os.walk(base, followlinks=False):
            current_path = Path(current)
            for name in list(directories):
                candidate = current_path / name
                if candidate.is_symlink():
                    raise ValueError(f"Unexpected symlink in OneROM source tree: {candidate}")
            for name in filenames:
                candidate = current_path / name
                if candidate.is_symlink() or not stat.S_ISREG(candidate.stat().st_mode):
                    raise ValueError(f"Unexpected non-regular OneROM source: {candidate}")
                key = candidate.relative_to(source_root).as_posix()
                if key in found:
                    raise ValueError(f"Duplicate fetched OneROM path: {key}")
                found[key] = candidate
    return found


def _verify_source_tree(source_root: Path, rows: list[dict]) -> dict[str, Path]:
    source_root = Path(source_root).resolve(strict=True)
    if not source_root.is_dir():
        raise ValueError("Fetched OneROM source root is not a directory")
    found = _source_files(source_root)
    expected = {row["upstream_path"]: row for row in rows}
    if set(found) != set(expected):
        missing = sorted(set(expected) - set(found))
        extra = sorted(set(found) - set(expected))
        raise ValueError(f"Fetched OneROM tree differs from its manifest (missing={missing[:3]}, extra={extra[:3]})")
    for upstream, entry in expected.items():
        size, blob_sha = _git_blob(found[upstream])
        if size != entry["size_bytes"] or blob_sha != entry["source_blob_sha1"]:
            raise ValueError(f"Pinned OneROM source blob differs: {upstream}")
    return found


def _git(args: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, check=True, text=True,
                            stdout=subprocess.PIPE, stderr=None)
    return result.stdout.strip()


def fetch_pinned_sources(destination: Path) -> Path:
    """Fetch just the two requested directories using Git's blob filter/sparse checkout."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    _git(["init", "--quiet", str(destination)])
    _git(["-C", str(destination), "remote", "add", "origin", UPSTREAM_URL])
    _git(["-C", str(destination), "config", "core.sparseCheckout", "true"])
    _git(["-C", str(destination), "config", "core.sparseCheckoutCone", "true"])
    _git(["-C", str(destination), "config", "remote.origin.promisor", "true"])
    _git(["-C", str(destination), "config", "remote.origin.partialclonefilter", "blob:none"])
    sparse = destination / ".git/info/sparse-checkout"
    sparse.write_text("/*\n!/*/\n/target/\n/target/beyond1lte/\n/platform/\n/platform/exynos9820/\n")
    _git(["-C", str(destination), "-c", "protocol.version=2", "fetch", "--quiet",
          "--no-tags", "--depth=1", "--filter=blob:none", "origin", UPSTREAM_COMMIT])
    _git(["-C", str(destination), "checkout", "--quiet", "--detach", "FETCH_HEAD"])
    head = _git(["-C", str(destination), "rev-parse", "HEAD"])
    if head != UPSTREAM_COMMIT:
        raise ValueError("Fetched OneROM HEAD does not match the approved commit")
    return destination


def _safe_destination(root: Path, relative: PurePosixPath) -> Path:
    path = root
    for component in relative.parts[:-1]:
        path = path / component
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError(f"Unsafe OneROM destination parent: {path}")
    destination = root.joinpath(*relative.parts)
    if destination.is_symlink() or (destination.exists() and not destination.is_file()):
        raise ValueError(f"Unsafe OneROM destination: {destination}")
    if not destination.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"OneROM destination escaped workspace: {destination}")
    return destination


def _copy_reference_material(reference: Path, manifest_path: Path, repo_root: Path) -> None:
    candidate_root = repo_root / "reference/onerom-port-candidates"
    license_path = candidate_root / "LICENSE"
    size, digest = _git_blob(license_path)
    if digest != LICENSE_BLOB_SHA1 or size != 35_147:
        raise ValueError("Retained OneROM GPL license differs from its pinned upstream blob")
    shutil.copy2(license_path, reference / "LICENSE")
    for source, name in (
        (candidate_root / "CREDITS.md", "CREDITS.md"),
        (candidate_root / "SNAPSHOT-README.md", "README.md"),
        (manifest_path, "onerom-source-snapshot.json"),
    ):
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Missing OneROM provenance file: {source}")
        shutil.copy2(source, reference / name)


def _module_state(rows: list[dict], source_root: Path) -> tuple[list[str], list[str]]:
    modules = set()
    disabled = set()
    for row in rows:
        parts = PurePosixPath(row["upstream_path"]).parts
        if len(parts) >= 5 and parts[2] == "patches":
            module = "/".join(parts[:4])
            modules.add(module)
            if (source_root / module / "disable").is_file():
                disabled.add(module)
    return sorted(modules), sorted(disabled)


def merge_verified_tree(workspace: Path, source_root: Path, manifest: dict,
                        *, manifest_path: Path | None = None,
                        repo_root: Path = ROOT,
                        require_pinned_inventory: bool = False) -> dict:
    """Overlay verified source blobs, retaining overwritten Artisan bytes and installer boundaries."""
    workspace = Path(workspace).resolve(strict=True)
    if not workspace.is_dir():
        raise ValueError("OneROM destination is not a workspace directory")
    manifest_path = Path(manifest_path or ROOT / "manifests/onerom-source-snapshot.json")
    rows = _entries(manifest, require_pinned_inventory=require_pinned_inventory)
    source_files = _verify_source_tree(Path(source_root), rows)

    reference = workspace / "reference"
    if reference.is_symlink() or (reference.exists() and not reference.is_dir()):
        raise ValueError("Unsafe workspace reference directory")
    upstream_destination = reference / "onerom-upstream"
    artisan_destination = reference / "artisan-before-onerom"
    for path in (upstream_destination, artisan_destination):
        if path.exists() or path.is_symlink():
            raise ValueError(f"Refusing to overwrite existing OneROM provenance: {path}")

    staging = Path(tempfile.mkdtemp(prefix=".onerom-port-", dir=workspace))
    overlay_root = staging / "overlay"
    reference_root = staging / "reference/onerom-upstream"
    backup_root = staging / "reference/artisan-before-onerom"
    reference_root.mkdir(parents=True)
    overlay_records = []
    identical = 0
    identical_paths = []
    new_files = 0
    new_paths = []
    overwritten = 0
    overwritten_paths = []
    protected = []
    source_shadows = []
    created_directories = []
    committed = []
    references_committed = []

    try:
        _copy_reference_material(reference_root, manifest_path, Path(repo_root))
        for row in rows:
            upstream = row["upstream_path"]
            relative = PurePosixPath(upstream)
            source = source_files[upstream]
            if upstream in UPSTREAM_SHADOW_PATHS:
                shadow = reference_root.joinpath(*relative.parts)
                shadow.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, shadow)
                source_shadows.append(upstream)
            if upstream in PROTECTED_ACTIVE_PATHS:
                # The full OneROM postinstall is retained with provenance, but is
                # deliberately not put in the active Artisan install recipe.
                protected.append(upstream)
                continue

            destination = _safe_destination(workspace, relative)
            source_mode = stat.S_IMODE(source.stat().st_mode)
            exists = destination.exists()
            if exists:
                size, digest = _git_blob(destination)
                if size == row["size_bytes"] and digest == row["source_blob_sha1"] \
                        and stat.S_IMODE(destination.stat().st_mode) == source_mode:
                    identical += 1
                    identical_paths.append(upstream)
                    continue
                backup = backup_root.joinpath(*relative.parts)
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destination, backup)
                overwritten += 1
                overwritten_paths.append(upstream)
            else:
                new_files += 1
                new_paths.append(upstream)
            staged = overlay_root.joinpath(*relative.parts)
            staged.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, staged)
            overlay_records.append((relative, staged, exists))

        modules, disabled_modules = _module_state(rows, Path(source_root))
        receipt = {
            "repository": UPSTREAM_REPOSITORY,
            "commit": UPSTREAM_COMMIT,
            "license": "GPL-3.0-or-later; per-file notices retained",
            "target": "SM-G973F / beyond1lte",
            "status": "complete-workspace-port-unvalidated",
            "source_files_verified": len(rows),
            "source_bytes_verified": sum(row["size_bytes"] for row in rows),
            "new_files": new_files,
            "new_paths": sorted(new_paths),
            "overwritten_artisan_files": overwritten,
            "overwritten_artisan_paths": sorted(overwritten_paths),
            "identical_artisan_files": identical,
            "identical_artisan_paths": sorted(identical_paths),
            "protected_from_active_installer": protected,
            "upstream_sources_preserved_before_project_adaptation": sorted(source_shadows),
            "integrated_patch_modules": modules,
            "upstream_disabled_modules": disabled_modules,
            "module_disable_markers_preserved": True,
            "one_rom_postinstall_active": False,
            "active_installer": "Artisan",
            "recovery_modified": False,
            "functional_validation_performed": False,
        }
        (reference_root / "PORT-RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")

        # Recheck every destination before the first workspace mutation.
        for relative, _staged, _exists in overlay_records:
            _safe_destination(workspace, relative)
        if reference.is_symlink() or (reference.exists() and not reference.is_dir()):
            raise ValueError("Unsafe workspace reference directory")

        if not reference.exists():
            reference.mkdir()
            created_directories.append(reference)
        for relative, staged, existed in overlay_records:
            destination = workspace.joinpath(*relative.parts)
            parent = destination.parent
            missing = []
            cursor = parent
            while not cursor.exists():
                missing.append(cursor)
                cursor = cursor.parent
            for directory in reversed(missing):
                directory.mkdir()
                created_directories.append(directory)
            os.replace(staged, destination)
            committed.append((relative, existed))

        os.replace(reference_root, upstream_destination)
        references_committed.append(upstream_destination)
        if backup_root.exists() and any(backup_root.rglob("*")):
            os.replace(backup_root, artisan_destination)
            references_committed.append(artisan_destination)
        shutil.rmtree(staging, ignore_errors=True)
        return receipt
    except Exception:
        backup_source = artisan_destination if artisan_destination.exists() else backup_root
        for relative, existed in reversed(committed):
            destination = workspace.joinpath(*relative.parts)
            try:
                if existed:
                    saved = backup_source.joinpath(*relative.parts)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(saved, destination)
                else:
                    destination.unlink(missing_ok=True)
            except OSError:
                pass
        for path in reversed(references_committed):
            shutil.rmtree(path, ignore_errors=True)
        for directory in reversed(created_directories):
            try:
                directory.rmdir()
            except OSError:
                pass
        shutil.rmtree(staging, ignore_errors=True)
        raise


def import_onerom_sources(workspace: Path, codename: str,
                          *, source_root: Path | None = None,
                          manifest_path: Path | None = None) -> dict | None:
    """Fetch, verify and merge the complete OneROM S10/Exynos tree for beyond1lte only."""
    if codename != "beyond1lte":
        return None
    manifest_path = Path(manifest_path or ROOT / "manifests/onerom-source-snapshot.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = _entries(manifest, require_pinned_inventory=True)
    if source_root is None:
        with tempfile.TemporaryDirectory(prefix="onerom-source-") as temporary:
            checkout = fetch_pinned_sources(Path(temporary) / "repo")
            return merge_verified_tree(
                workspace, checkout, manifest, manifest_path=manifest_path,
                repo_root=ROOT, require_pinned_inventory=True)
    return merge_verified_tree(
        workspace, Path(source_root), manifest, manifest_path=manifest_path,
        repo_root=ROOT, require_pinned_inventory=True)


if __name__ == "__main__":
    raise SystemExit("Import this module from scripts/prepare_workspace.py; it does not build or flash a ROM.")
