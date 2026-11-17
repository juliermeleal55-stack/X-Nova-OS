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

The default CLI target remains beyond1lte/SM-G973F. A separate, unvalidated
candidate workflow now requests beyond2lte/SM-G975F through the Alpha 3.2
TWRP/RAW ZIP path, with the structure-only profile and no fixed image-size
limits. It uses the existing S10 RAW-image packaging format; the pinned
ExtremeROM repartitioner contributes generic partition names only, not size
values or evidence of the G975F physical layout/ArtisanROM compatibility. This
is a build request, not a completed or hardware-supported ROM; see
[S10+ OTA research](S10PLUS-OTA-RESEARCH.md).

Generated markers contain model AND codename. Wrappers reject mismatched/unknown
markers; package names and model assertions are device-specific. The S10+ path
is restricted to SM-G975F/beyond2lte, and does not include SM-G975N or Snapdragon
variants.

The primary S10 alpha workflow is **manual** (`workflow_dispatch`) with a target
selector. The separate S10+ request workflow is path-triggered on its own file;
this workspace has not pushed it or launched an Actions build. Source validation
still runs on pushes and pull requests. No device build was launched as part of
adding the primary S10 target.

Validation in this step: unit tests for own stock configuration, target routing,
model mismatch rejection, legacy markers, distinct package names and warnings.
This does not validate firmware download, patch application or physical boot.
The existing storage/extraction problems and unverified donor properties also
apply to this target. No flashable S10 ROM is claimed.
