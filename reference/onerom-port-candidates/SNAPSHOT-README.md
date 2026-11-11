# OneROM S10/Exynos source import

The pinned OneROM revision is `DaDevMikey/OneROM` at
`644f0aacc49ad2410e566de8deb05e6c8211d83d`. This project imports the complete
`target/beyond1lte/` and `platform/exynos9820/` trees into fresh
**SM-G973F / beyond1lte** workspaces while preserving Artisan as the base.

## Source inventory and workspace behavior

- `manifests/onerom-source-snapshot.json` contains metadata for all **474**
  upstream blobs: **283 text/source files** (1,325,836 bytes) retained
  byte-for-byte in this repository and **191 non-text/unclassified assets**
  (324,683,033 bytes) fetched only when a workspace is prepared.
- The importer uses a pinned partial Git fetch and sparse checkout for the two
  scoped directories, checks every upstream path, byte size and Git blob SHA-1,
  then merges all files into the actual target/platform trees. Binary payloads
  remain outside this Git repository.
- Original Artisan bytes for files replaced by OneROM are captured in
  `reference/artisan-before-onerom/`; exact OneROM copies of project-adapted
  files and the protected OneROM postinstall recipe are kept in
  `reference/onerom-upstream/`. A `PORT-RECEIPT.json` records imported paths,
  counts, modules, provenance and integration boundaries.
- OneROM module `disable` markers remain byte-for-byte and in place. The
  separate project-authored `search_indexing/adapt_candidate.py` remains
  review-only and is not enabled by the importer.
- The OneROM `target/beyond1lte/postinstall.edify` is retained as provenance but
  is **not** copied over Artisan's active installation recipe. The Artisan
  installer remains active; the import does not alter recovery, publish a ROM,
  flash a device, or claim functional validation.

Credits, module authors and licensing boundaries are in [`CREDITS.md`](CREDITS.md)
and [`LICENSE`](LICENSE). GPL-3.0-or-later applies to the upstream GPL-covered
source; proprietary vendor/APK/image assets may be subject to separate terms.
Do not redistribute those assets solely on the basis of the GPL source license.

## Snapshot chronology

The pinned repository/commit dates are later than the recorded session date
`2026-10-30`. The user explicitly approved proceeding with this exact revision;
the dates are retained as reported and are not rewritten as contemporaneous.
