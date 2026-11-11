# OneROM Settings

Native XML-backed Settings pages adapted from OneROM-patches revision `e03a70f63d8256d73bc67887fcf1322942c888fa`:
https://github.com/DaDevMikey/OneROM-patches

The selected resources, translations, banner layouts, preference controllers, Bixby trampoline, and resource utilities are imported from `unica/mods/settings`. Preserve their upstream attribution. The old all-in-one module remains disabled because its unrelated framework and security modifications have not been ported.

`prepare.py` merges resource items with Python's XML parser, stages the selected controllers, and adds a real OneROM entry to the Settings homepage. About phone and Software information use the legacy wallpaper banner. The OneROM root, UI, and Extra options fragments inflate native XML resources; no reflection-generated menu or Settings code-override archive is used.

Included controls cover custom banner text, software/build identity, developer-options entry, single/double/hold Bixby actions, and Settings identifier visibility. The visibility switches mask the shared Samsung IMEI/serial getters; they do not alter telephony identifiers or other applications. Samsung's existing software-information controllers remain in use. Battery menu model gates are adapted, but measured battery wear still requires actual fuel-gauge support.

Guide, changelog, credits/instructions, updater pages, integrity spoofing, keybox management, and unrelated legacy application/security bypasses are excluded from the installed UI. The older global settings module must not be enabled as well.

## Signing

Settings is rebuilt and signed using the configured project platform certificate. The repaired `unica/patches/signature` patch now limits its compatibility path to all three conditions:

- Package name is exactly `com.android.settings`.
- Base APK path is exactly `/system/priv-app/SecSettings/SecSettings.apk`.
- Actual APK certificate matches the configured project platform certificate.

Only that system APK receives platform signing-details normalization during boot scanning, allowing its existing Samsung system shared UID to be retained. Data-installed APKs, other package names, wrong paths, and other certificates do not qualify. This changes package-manager trust for Settings and must be tested with its paired services JAR. Other protected Samsung applications retain their original APKs and existing version-bound compatibility overrides.

## Validation

The selected controller DEX, current-donor signature patch, resource importer, and full native Settings APK have focused build checks. Full builds must include the paired services patch, rebuilt Settings APK, Bixby InputRune flags, keylayouts, and Delta identity properties.

On hardware, verify normal boot/package scanning, the Settings homepage, About phone, Software information, all three OneROM pages, banner editing/back navigation, both privacy switches, and physical Bixby actions. Keep a recovery backup of the preceding services JAR and Settings APK. Do not mix the rebuilt APK with an older unpatched services JAR.