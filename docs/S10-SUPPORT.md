# Galaxy S10 normal — candidate Exynos support

Added target: **beyond1lte / SM-G973F**. This is not support for SM-G973U/U1/W/0
or other Snapdragon variants. The user's exact model has not yet been confirmed.
SM-G973N is also deliberately excluded from assertions until separately validated.

The pinned ArtisanROM archive already includes its own beyond1lte tree, overlays,
camera modules, sff.sh and postinstall. The preparer preserves that tree instead
of cloning the S10+ target. Stock firmware remains SM-G973F/AUT, Exynos 9820,
vendor API/VNDK 31, static ext4, 60 Hz. Platform patches and the donor adapter
are shared with the Exynos S10+, but the kernel build receives beyond1lte.

```bash
python3 scripts/prepare_workspace.py /outside/repo/s10-work --target beyond1lte
python3 scripts/init_workspace_dependencies.py /outside/repo/s10-work
bash scripts/build_smart_downloader.sh /outside/repo/s10-work
bash scripts/probe_firmware.sh /outside/repo/s10-work
bash scripts/build_candidate.sh /outside/repo/s10-work dependencies
bash scripts/build_candidate.sh /outside/repo/s10-work alpha
python3 scripts/collect_alpha.py /outside/repo/s10-work /outside/repo/s10-result
python3 scripts/port.py doctor --target beyond1lte
```

The default CLI target remains beyond1lte/SM-G973F. The separate SM-G975F /
beyond2lte request uses the same successful S10 Alpha 3.2 full-build settings,
including `content-sized`, the pinned S24 FE donor, Artisan base and shared
TWRP/RAW ZIP pipeline; only the exact target-specific assets and installer
assertion are adapted. OneROM patches explicitly scoped to beyond1lte are not
copied to beyond2lte; the common compatibility pieces remain source-pinned.
There are no fixed image-size caps. The installer checks actual image sizes
against current target capacities read-only and never repartitions or formats.
The physical G975F partition table and boot remain unverified. Build #7 failed
while resolving a Gradle plugin before packaging; the retry, Build #8, passed
build-tools compilation and was downloading firmware at last check. No S10+ ZIP
has been validated yet; see [S10+ OTA research](S10PLUS-OTA-RESEARCH.md).

Generated markers contain model AND codename. Wrappers reject mismatched/unknown
markers; package names and model assertions are device-specific. The S10+ path
is restricted to SM-G975F/beyond2lte, and does not include SM-G975N or Snapdragon
variants.

The primary S10 alpha workflow is **manual** (`workflow_dispatch`) with a target
selector. The separate S10+ request workflow is path-triggered on its own file;
this branch has pushed the full experimental request. The S10+ Actions result
must be checked before claiming a package; source validation also runs on pushes
and pull requests. No device flash or boot validation is claimed.

Validation in this step: unit tests for own stock configuration, target routing,
model mismatch rejection, legacy markers, distinct package names and warnings.
This does not validate firmware download, patch application or physical boot.
The existing storage/extraction problems and unverified donor properties also
apply to this target. No flashable S10 ROM is claimed.
