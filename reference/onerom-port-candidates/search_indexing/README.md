# Search-indexing adapter — review-only candidate

**Status: the project-authored adapter is not integrated, not enabled and not
validated against the actual donor APK.** This directory remains under
`reference/`; workspace preparation does not copy this adapter. Separately, the
full upstream OneROM S10 tree is imported into fresh `beyond1lte` workspaces;
its original `search_indexing` module is copied with its upstream `disable`
marker preserved, so the upstream patch is not executed by the module runner.

## Provenance and credits

- Upstream: [DaDevMikey/OneROM](https://github.com/DaDevMikey/OneROM)
- Audited snapshot: `644f0aacc49ad2410e566de8deb05e6c8211d83d`
- Upstream file:
  `target/beyond1lte/patches/search_indexing/smali/system/priv-app/SecSettingsIntelligence/SecSettingsIntelligence.apk/0001-Skip-absent-policy-resource-IDs.patch`
- Upstream Git blob SHA-1: `7add52275f17c126d019029809fcd82d13a073a1`
- Retained patch SHA-256: `bfa847f8333636019773d46d203b35b65c94fd3a8acdfa916c9e292af3534081`
- Upstream repository commit author/integrator: **DaManMikey**. The upstream
  module metadata credits **UN1CA contributors**. No OneROM-derived code is
  presented as Julier's or X-Nova OS's original code.
- License: **GPL-3.0-or-later**. The accompanying `../LICENSE` retains the
  upstream license text.

The pinned source is future-dated relative to the recorded session date
`2026-10-30`: GitHub reports the repository created `2026-11-03`, the initial
S10 port commit dated `2026-11-02`, and this audited commit dated `2026-11-05`.
The user explicitly chose to proceed with this exact snapshot despite that
chronology; the dates are recorded, not rewritten.

## Patch and project-authored adapter

The upstream patch attempts a narrow guard in `DevicePolicyResourcesUtils`:
when the resource ID returned by `TypedArray.getResourceId()` is the absent-ID
sentinel, return `false` before calling `Resources.getResourceEntryName()`.
That leaves the existing `XmlParserUtils.getData()` / `TypedArray.getString()`
fallback for literal and absent XML values intact and valid resource-ID
lookups on their original path.

`adapt_candidate.py` is a separate project-authored, fail-closed tool. It writes
a **new output file** and refuses to overwrite its input. Before inserting the
guard it requires the exact class, one boolean method/lookup, adjacent
`getResourceId()` result flow, an explicit `-1` default register immediately
before the call, matching resource-ID registers and a low register for the
early `false` return. Unsupported or ambiguous donor Smali is rejected; the
original upstream patch is retained unchanged for provenance.

The adapter's structural checks and the upstream hunk were exercised only
against synthetic host fixtures. No donor APK was obtained or decoded, and no
adapter output was applied to donor code, rebuilt into an APK, or run on an
SM-G973F device. **These are gates for enabling this adapter only; the user-
requested full source-tree port does not wait on these adapter checks.**

## Other OneROM modules and activation state

The full target/platform tree is imported separately with every upstream
`disable` marker retained. `search_indexing`, `usb_initialization`,
`user_defaults` and `wallpaper_capture` remain disabled because their upstream
module directories contain `disable` markers. `product_abilist` and the
upstream modules that lack such markers are imported according to their
upstream state; no functional compatibility claim is made. Their scripts,
resources and binary assets are covered by the full-tree inventory and
workspace receipt, not by this adapter.

The OneROM `target/beyond1lte/postinstall.edify` is kept as provenance rather
than installed over Artisan's active postinstall recipe. The Artisan installer
remains active; recovery is not modified. See [`ONEROM-AUDIT.md`](../../../docs/ONEROM-AUDIT.md)
for complete import behavior, attribution and redistribution boundaries.
