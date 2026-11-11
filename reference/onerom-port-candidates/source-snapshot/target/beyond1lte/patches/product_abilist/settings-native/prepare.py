from copy import deepcopy
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET


ANDROID = "{http://schemas.android.com/apk/res/android}"
SETTINGS = "{http://schemas.android.com/apk/res-auto}"
ET.register_namespace("android", ANDROID[1:-1])
ET.register_namespace("settings", SETTINGS[1:-1])


def write_xml(root, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def prepare(module, decoded):
    assets = module / "SecSettings.apk"
    package = decoded / "smali_classes5/io/mesalabs/unica/settings"
    if package.exists():
        shutil.rmtree(package)

    # 1. Clear any old reflection hooks
    for path in (
        decoded / "smali/com/android/settings/SettingsActivity.smali",
        decoded / "smali_classes3/com/samsung/android/settings/deviceinfo/aboutphone/SecMyDeviceInfoFragment.smali",
        decoded / "smali_classes3/com/samsung/android/settings/deviceinfo/softwareinfo/SoftwareInfoSettings.smali",
        decoded / "smali_classes3/com/samsung/android/settings/deviceinfo/SecDeviceInfoUtils.smali",
    ):
        if not path.exists():
            continue
        source = path.read_text()
        source = re.sub(
            r"    invoke-static \{p1\}, Lio/mesalabs/unica/settings/OneRomSettings;->isOneRomFragment.*?:onerom_existing_fragment_validation\n",
            "", source, flags=re.S,
        )
        source = re.sub(r"    invoke-static \{p0\}, Lio/mesalabs/unica/settings/OneRomSettings;->attach[^\n]+\n", "", source)
        source = re.sub(
            r'    const-string v0, "onerom_show_(imei|serial)"\n    invoke-static \{p0, v0\}, Lio/mesalabs/unica/settings/OneRomSettings;->showIdentifier.*?    :onerom_show_\1\n',
            "", source, flags=re.S,
        )
        path.write_text(source)

    # 2. Copy and merge all XML and drawables from assets
    for source in (assets / "res").rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(assets)
        destination = decoded / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if relative.parts[1].startswith("values") and source.suffix == ".xml":
            target = ET.parse(destination).getroot() if destination.exists() else ET.Element("resources")
            keys = {(item.tag, item.get("name")) for item in target}
            for item in ET.parse(source).getroot():
                if (item.tag, item.get("name")) not in keys:
                    target.append(deepcopy(item))
                    keys.add((item.tag, item.get("name")))
            write_xml(target, destination)
        else:
            shutil.copy2(source, destination)

    # 3. Copy full smali_classes5 tree
    shutil.copytree(assets / "smali_classes5", decoded / "smali_classes5", dirs_exist_ok=True)

    # 4. Replace 8.0, 8.5 references with 9.0 in smali
    for path in (decoded / "smali_classes5").rglob("*.smali"):
        source = path.read_text()
        source = source.replace("OneROM 8.0", "OneROM 9.0")
        source = source.replace("OneROM 8.5", "OneROM 9.0")
        source = source.replace("OneROM Native", "OneROM Delta")
        path.write_text(source)

    # 5. Fix logo layout text
    logo_layout = decoded / "res/layout/unica_settings_logo_layout.xml"
    if logo_layout.exists():
        src = logo_layout.read_text()
        src = re.sub(r'android:text="OneROM[^"]*"', 'android:text="OneROM Delta 9.0"', src)
        logo_layout.write_text(src)

    # 6. Update strings
    for strings_path in decoded.glob("res/values*/strings.xml"):
        try:
            strings = ET.parse(strings_path).getroot()
            modified = False
            for item in strings:
                if item.get("name") == "onerom_banner_default":
                    item.text = "OneROM 9.0"
                    modified = True
            for name, value in {
                "onerom_delta_title": "OneROM features",
                "onerom_delta_summary": "9.0",
                "onerom_show_imei_title": "Show IMEI",
                "onerom_show_serial_title": "Show serial number",
            }.items():
                item = next((entry for entry in strings if entry.get("name") == name), None)
                if item is None:
                    item = ET.SubElement(strings, "string", {"name": name})
                item.text = value
                modified = True
            if modified:
                write_xml(strings, strings_path)
        except Exception:
            pass

    # 7. Main Settings Homepage: REMOVE OneROM entry
    # (Requirement: in the main settings page there should NOT be a onerom option, shortcut belongs in software info)
    homepage_path = decoded / "res/xml/sec_top_level_settings.xml"
    if homepage_path.exists():
        homepage = ET.parse(homepage_path).getroot()
        changed = False
        for item in list(homepage):
            if item.get(ANDROID + "key") in {"top_level_onerom", "onerom_guide"}:
                homepage.remove(item)
                changed = True
        if changed:
            write_xml(homepage, homepage_path)

    # 8. Ensure Software Info Settings has banner and OneROM settings shortcut
    software_xml_path = decoded / "res/xml/sec_software_info_settings.xml"
    if software_xml_path.exists():
        software = ET.parse(software_xml_path).getroot()
        # Ensure banner is present
        if not any(item.get(ANDROID + "key") == "onerom_software_banner" for item in software):
            banner = ET.Element("com.android.settingslib.widget.LayoutPreference", {
                ANDROID + "layout": "@layout/onerom_software_banner",
                ANDROID + "selectable": "true",
                ANDROID + "key": "onerom_software_banner",
                ANDROID + "order": "-999",
                ANDROID + "fragment": "io.mesalabs.unica.settings.UnicaSettingsFragment",
                SETTINGS + "controller": "io.mesalabs.unica.settings.SoftwareInfoBannerPreferenceController",
                SETTINGS + "searchable": "false",
            })
            software.insert(0, banner)
            write_xml(software, software_xml_path)

    # 9. Also add banner to About phone if desired
    about_fragment = decoded / "smali_classes3/com/samsung/android/settings/deviceinfo/aboutphone/SecMyDeviceInfoFragment.smali"
    if about_fragment.exists():
        match = re.search(r"\.method public final getPreferenceScreenResId\(\)I.*?const p0, (0x[0-9a-f]+)",
                          about_fragment.read_text(), re.S)
        if match:
            public = ET.parse(decoded / "res/values/public.xml").getroot()
            resource = next((item.get("name") for item in public
                            if item.get("type") == "xml" and item.get("id") == match.group(1)), None)
            if resource:
                about_path = decoded / f"res/xml/{resource}.xml"
                if about_path.exists():
                    about = ET.parse(about_path).getroot()
                    if not any(item.get(ANDROID + "key") == "onerom_software_banner" for item in about):
                        software = ET.parse(software_xml_path).getroot()
                        banner_item = next((item for item in software if item.get(ANDROID + "key") == "onerom_software_banner"), None)
                        if banner_item is not None:
                            about.insert(0, deepcopy(banner_item))
                            write_xml(about, about_path)

    # 10. Battery Regulatory & Health: FORCE AVAILABLE
    for path in decoded.glob("smali*/com/samsung/android/settings/deviceinfo/batteryinfo/BatteryInfoUtils.smali"):
        source = path.read_text()
        pat = r"(\.method public static isAvailableBatteryRegulatory\(Landroid/content/Context;\)Z\n)(.*?)(\.end method)"
        rep = r"\1    .locals 1\n    const/4 v0, 0x1\n    return v0\n\3"
        source = re.sub(pat, rep, source, flags=re.S)
        path.write_text(source)

    for name in ("BatteryRegulatoryPreferenceController", "SecBatteryInfoFragment", "BatteryHealthPreferenceController"):
        for path in decoded.glob(f"smali*/com/samsung/android/settings/deviceinfo/batteryinfo/{name}.smali"):
            source = path.read_text()
            source = source.replace('"SM-A236B"', '"SM-S721B"')
            path.write_text(source)

    # 11. Build Number Branding: Ensure it always displays custom OneROM branding with source build number
    for path in decoded.glob("smali*/com/android/settings/deviceinfo/BuildNumberPreferenceController.smali"):
        source = path.read_text()
        pat = r"(\.method public getSummary\(\)Ljava/lang/CharSequence;\n)(.*?)(\.end method)"
        rep = (
            r"\1    .locals 2\n"
            r'    const-string v0, "ro.build.display.id"\n'
            r'    const-string v1, "OneROM Delta 9.0 (beyond1lte) (S721BXXSFEZJ1)"\n'
            r"    invoke-static {v0, v1}, Landroid/os/SemSystemProperties;->get(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;\n"
            r"    move-result-object v0\n"
            r"    return-object v0\n\3"
        )
        source = re.sub(pat, rep, source, flags=re.S)
        path.write_text(source)


    # 12. Register activities in AndroidManifest.xml
    manifest_path = decoded / "AndroidManifest.xml"
    manifest = ET.parse(manifest_path).getroot()
    application = manifest.find("application")
    activity = "io.mesalabs.unica.BixbyKeyActionActivity"
    if not any(item.get(ANDROID + "name") == activity for item in application.findall("activity")):
        ET.SubElement(application, "activity", {
            ANDROID + "name": activity, ANDROID + "exported": "false",
            ANDROID + "excludeFromRecents": "true", ANDROID + "noHistory": "true",
            ANDROID + "taskAffinity": "", ANDROID + "showWhenLocked": "true",
            ANDROID + "theme": "@android:style/Theme.Translucent.NoTitleBar",
        })
    write_xml(manifest, manifest_path)

    # 13. SettingsActivity: Validate all Unica / OneROM fragments
    activity_path = decoded / "smali/com/android/settings/SettingsActivity.smali"
    if activity_path.exists():
        source = activity_path.read_text()
        if ":onerom_native_fragment" not in source:
            anchor = ".method public isValidFragment(Ljava/lang/String;)Z\n    .locals 4"
            if anchor in source:
                checks = (
                    '\n    const-string v0, "io.mesalabs.unica.settings."\n'
                    "    invoke-virtual {p1, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z\n"
                    "    move-result v0\n"
                    "    if-eqz v0, :onerom_native_fragment\n"
                    "    goto :onerom_standard_fragment\n"
                    "    :onerom_native_fragment\n"
                    "    const/4 v0, 0x1\n"
                    "    return v0\n"
                    "    :onerom_standard_fragment\n"
                )
                source = source.replace(anchor, anchor + checks, 1)
                activity_path.write_text(source)

    # 14. IMEI and Serial privacy masking in SecDeviceInfoUtils.smali
    utils_path = decoded / "smali_classes3/com/samsung/android/settings/deviceinfo/SecDeviceInfoUtils.smali"
    if utils_path.exists():
        source = utils_path.read_text()
        for identity, signature in (
            ("imei", "getImei(Landroid/content/Context;IZ)Ljava/lang/String;"),
            ("serial", "getSerialNumber(Landroid/content/Context;)Ljava/lang/String;"),
        ):
            if f":onerom_show_{identity}" in source:
                continue
            pattern = rf"(\.method public static {re.escape(signature)}\n    \.locals )(\d+)"
            def inject(match):
                return match.group(1) + str(max(3, int(match.group(2)))) + f'''

    invoke-virtual {{p0}}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v0
    const-string v1, "onerom_show_{identity}"
    const/4 v2, 0x1
    invoke-static {{v0, v1, v2}}, Landroid/provider/Settings$System;->getInt(Landroid/content/ContentResolver;Ljava/lang/String;I)I
    move-result v0
    if-nez v0, :onerom_show_{identity}
    const-string v0, "********"
    return-object v0
    :onerom_show_{identity}'''
            source, count = re.subn(pattern, inject, source)
            if count != 1:
                pass
        utils_path.write_text(source)


if __name__ == "__main__":
    prepare(Path(sys.argv[1]), Path(sys.argv[2]))
