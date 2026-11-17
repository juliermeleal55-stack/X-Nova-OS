# OneROM attribution and provenance — SM-G975F / beyond2lte

This X-Nova OS candidate uses the pinned OneROM project as a limited shared Exynos 9820 compatibility reference: `DaDevMikey/OneROM` at commit `644f0aacc49ad2410e566de8deb05e6c8211d83d`. The source snapshot's commit author/integrator is credited as **DaManMikey**. The shared `platform/exynos9820/patches/miscs` module records **salvo_giangri** and **ExtremeXT** in its upstream author field.

The beyond2lte workspace does **not** import or activate OneROM's `target/beyond1lte/` patch modules. This notice credits the shared project references used by the integration; it does not claim that every module in the full OneROM snapshot is present in this S10+ package. The package provenance manifest records the exact OneROM source commit.

The OneROM README credits **Creeeeger** for the Exynos 9820 kernel lineage, **ArtisanROM** for its kernel/vendor bring-up reference, and the **KernelSU Next Team** for root integration. Preserve each project's original notices. The applicable GPL-3.0-or-later license text is included separately at `LICENSES/GPL-3.0-or-later.txt`; proprietary firmware and vendor assets remain subject to their own terms.

These attributions are not a claim of SM-G975F compatibility, safe installation, or hardware boot validation.
