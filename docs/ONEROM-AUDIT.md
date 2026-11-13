# OneROM S10 port and provenance

## Pinned source and scope

- Upstream: [DaDevMikey/OneROM](https://github.com/DaDevMikey/OneROM)
- Revision: `644f0aacc49ad2410e566de8deb05e6c8211d83d`
- The full upstream repository inventory contains 4,468 blobs / 2,169,646,717
  bytes. This S10 port imports the complete requested target/platform scope;
  unrelated `unica/`, generic `scripts/` and broad `prebuilts/` are not copied
  as additional build trees.
- License: GPL-3.0-or-later for the GPL-covered source; per-file and module
  notices are preserved. See [`CREDITS.md`](../reference/onerom-port-candidates/CREDITS.md)
  and the retained upstream [`LICENSE`](../reference/onerom-port-candidates/LICENSE).
- Target: **Galaxy S10 normal, SM-G973F / `beyond1lte`**; not the S10+.
- Imported trees: all of `target/beyond1lte/` and `platform/exynos9820/`.
- Exact inventory and Git blob identities:
  [`manifests/onerom-source-snapshot.json`](../manifests/onerom-source-snapshot.json).

## Workspace port behavior

Fresh `beyond1lte` workspaces fetch the exact commit with a filtered, sparse Git
checkout, verify every path, size and Git blob SHA-1, then merge all **474
files / 326,008,869 bytes** into the generated Artisan workspace. The two
scoped trees contain **283 text/source files** (1,325,836 bytes) and **191
non-text or unclassified assets** (324,683,033 bytes). The repository retains
the text snapshot and inventory; the larger assets are fetched into generated
workspaces and are not committed to Git.

The import is a full source port, not a claim of runtime compatibility. It
preserves the upstream module `disable` markers and module attribution. Existing
Artisan files that the OneROM tree replaces are saved under
`reference/artisan-before-onerom/` in the generated workspace. The exact OneROM
versions of files subsequently adapted by project integration, along with the
original OneROM postinstall recipe, are saved under
`reference/onerom-upstream/`; `PORT-RECEIPT.json` records the import counts and
boundaries.

The generated target remains restricted to **SM-G973F** by the existing
workspace adaptation. OneROM's `target/beyond1lte/postinstall.edify` is
preserved as provenance only; it does not replace Artisan's active installer
recipe. No OneROM recovery image or recovery code is installed or modified, and
this work does not publish or flash a ROM. The existing Artisan installer
remains the active installer.

## Imported modules and preserved upstream disable state

The normal target/platform patch directories are populated with the OneROM
modules and resources, including their source module metadata, scripts, patches,
configuration files, system/vendor files, APK/image/native assets and kernel
payloads. The import first retains every upstream `disable` marker byte-for-byte
and records the disabled module inventory.

For the **SM-G973F / `beyond1lte` build only**, workspace preparation then
activates the project-pinned `integration/artisan/extremekrnl.sh` replacement.
The module runner returns before sourcing `customize.sh` whenever its `disable`
marker exists; leaving that marker active skipped the kernel compiler. The
Alpha 3.2 #25 logs show stock target extraction supplied `boot.img` and
`dtbo.img`, but not `dtb.img`, so the later RAW packaging gate correctly stopped.
Preparation now preserves the exact OneROM marker at
`reference/onerom-upstream/platform/exynos9820/patches/extremekrnl/disable`,
removes only the active workspace marker, and installs the pinned hook. Its
pinned kernel revision must produce non-empty `boot.img`, `dtb.img`, and
`dtbo.img`; the existing RAW/ZIP validators still reject missing or malformed
images. The original OneROM binaries are not used as substitutes for these
pinned build outputs. This is not boot/runtime validation.

Other upstream markers remain active, including those on `extradim`,
`search_indexing`, `usb_initialization`, `user_defaults` and
`wallpaper_capture`. The separate project-authored
`search_indexing/adapt_candidate.py` remains review-only and outside the build.
The original upstream search-indexing module is copied with its upstream
`disable` marker intact. The fixture-based adapter checks do not constitute
donor APK/DEX or device tests.

## Credit and redistribution boundaries

The upstream commit author/integrator is **DaManMikey**. Module-level author
fields are reproduced in `CREDITS.md`; those fields are not expanded into
invented per-file authorship. **Julier is credited as creator of X-Nova OS; no
OneROM-derived code is attributed to Julier.**

The 191 non-text entries include proprietary/vendor binary assets. Their exact
blob metadata is retained, but GPL on the source files does not itself grant
redistribution rights for every APK, native library, image or boot payload.
They are fetched for the generated workspace as requested; no public release or
redistribution permission is implied.

## Validation record

Source integrity and tree completeness are checked during workspace
preparation. No donor APK or physical S10 validation is claimed here. The
requested port does not wait on functional validation; no ROM publication,
installer approval, recovery modification or flash is authorized by this
source import.
