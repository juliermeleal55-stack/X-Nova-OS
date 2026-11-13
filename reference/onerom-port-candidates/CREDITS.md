# OneROM S10 source port — credits and license notices

This project imports `DaDevMikey/OneROM` at commit
`644f0aacc49ad2410e566de8deb05e6c8211d83d` for the normal Galaxy S10 target
`SM-G973F / beyond1lte` and its `platform/exynos9820` tree. The upstream source
license is GPL-3.0-or-later; see [`LICENSE`](LICENSE). Original source headers,
module metadata and notices are retained in the imported files. Every imported
blob is checked against the Git tree SHA-1 and size recorded in
[`manifests/onerom-source-snapshot.json`](../../manifests/onerom-source-snapshot.json).

## Upstream repository and module credits

The reviewed OneROM snapshot's commit author/integrator is **DaManMikey**.
Credits below reproduce each upstream `module.prop` author field; they are not
claims that the listed people authored every file in that module.

| Upstream module | Upstream author field |
| --- | --- |
| `platform/exynos9820/patches/audio` | ExtremeXT, AlexFurina |
| `platform/exynos9820/patches/bixbykey` | ExtremeXT |
| `platform/exynos9820/patches/camera` | ExtremeXT |
| `platform/exynos9820/patches/extradim` | Ocin4ever |
| `platform/exynos9820/patches/extremekrnl` | ExtremeXT |
| `platform/exynos9820/patches/hrm` | duhansysl |
| `platform/exynos9820/patches/midas` | ExtremeXT |
| `platform/exynos9820/patches/miscs` | salvo_giangri, ExtremeXT |
| `platform/exynos9820/patches/stock_blobs` | ExtremeXT |
| `platform/exynos9820/patches/vendor` | ExtremeXT |
| `target/beyond1lte/patches/camera` | ExtremeXT |
| `target/beyond1lte/patches/edge_lighting` | salvogiangri |
| `target/beyond1lte/patches/product_abilist` | Robertgarciaa |
| `target/beyond1lte/patches/search_indexing` | UN1CA contributors |
| `target/beyond1lte/patches/usb_initialization` | ArtisanROM |
| `target/beyond1lte/patches/user_defaults` | ArtisanROM |
| `target/beyond1lte/patches/wallpaper_capture` | UN1CA contributors |

These credits are intentionally clear rather than replaced with an invented
credit count or authorship claim. **Julier is credited as creator of X-Nova OS;
no OneROM-derived code is attributed to Julier.**

## Kernel lineage and source attribution

The pinned OneROM project README credits **Creeeeger** for the Exynos 9820
Extreme Kernel CPU/GPU overclock and kernel tree, identifies the base as
ExtremeKRNL 2.6.5 (`openela-rc1`, Linux 4.14.356), and references
[the Exynos 9820 kernel source](https://github.com/Creeeeger/9820_kernel).
It also credits **ArtisanROM** for the kernel lineage/vendor bring-up reference
and the **KernelSU Next Team** for root integration. Preserve those upstream
attributions and the applicable kernel/KernelSU licenses; this is not a claim
that the X-NovaOS ROM or kernel has been validated on hardware.

## Complete workspace import and non-source assets

The Git repository keeps a compact byte-exact snapshot of **283 text/source
files** plus metadata for every blob in the two requested trees. When a fresh
`beyond1lte` workspace is prepared, the helper fetches the pinned commit using
Git's blob filter and sparse checkout, verifies **all 474 paths, sizes and Git
blob hashes**, and imports the full `target/beyond1lte/` and
`platform/exynos9820/` trees, including the 191 non-text or prebuilt assets. The
large payloads are fetched into the generated workspace rather than committed
to this repository.

The upstream module `disable` markers are preserved. The project-authored
search-indexing adapter remains review-only and is not wired into the build.
Original Artisan bytes for files replaced by OneROM are saved under
`reference/artisan-before-onerom/`; exact OneROM versions of project-adapted
files are saved under `reference/onerom-upstream/`. The OneROM
`target/beyond1lte/postinstall.edify` is retained there, not installed as the
active postinstall recipe. Artisan remains the active installer, and no
recovery image or recovery code is replaced by this import.

The inventory labels non-text blobs separately because their licenses may not
be GPL. Vendor/APK/image redistribution rights are not implied by the OneROM
source license or by including them in a locally generated workspace. Keep the
upstream path, blob identity, module author and applicable license intact; no
publication or flash authorization is inferred.
