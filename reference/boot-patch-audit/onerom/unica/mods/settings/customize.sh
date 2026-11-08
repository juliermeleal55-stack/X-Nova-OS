LOG_STEP_IN "- Adding ExtremeROM logo PNG"
DECODE_APK "system" "system/priv-app/SecSettings/SecSettings.apk"
cp -fa "$SRC_DIR/unica/mods/settings/SecSettings.apk/"* "$APKTOOL_DIR/system/priv-app/SecSettings/SecSettings.apk"
LOG_STEP_OUT

LOG_STEP_IN "- Enabling BSOH in SecSettings"

DECODE_APK "system" "system/priv-app/SecSettings/SecSettings.apk"

FTP="
system/priv-app/SecSettings/SecSettings.apk/smali_classes4/com/samsung/android/settings/deviceinfo/batteryinfo/BatteryRegulatoryPreferenceController.smali
system/priv-app/SecSettings/SecSettings.apk/smali_classes4/com/samsung/android/settings/deviceinfo/batteryinfo/SecBatteryInfoFragment.smali
"
for f in $FTP; do
    if [ -f "$APKTOOL_DIR/$f" ]; then
        sed -i "s/SM-A236B/SM-S721B/g" "$APKTOOL_DIR/$f"
    else
        _pkg_path="${f%%/smali*}"
        _target_file="$(find "$APKTOOL_DIR/$_pkg_path" -name "$(basename "$f")" 2>/dev/null | head -n 1)"
        if [ -n "$_target_file" ] && [ -f "$_target_file" ]; then
            sed -i "s/SM-A236B/SM-S721B/g" "$_target_file"
        fi
    fi
done
LOG_STEP_OUT

LOG_STEP_IN "- Enabling Cached App Freezer"
SET_PROP "system" "persist.device_config.activity_manager_native_boot.use_freezer" "true"
LOG_STEP_OUT

# ro.build.2ndbrand is always "false"
LOG_STEP_IN "- Disabling ASKS"
if [ -f "$APKTOOL_DIR/system/framework/services.jar/smali/com/android/server/asks/ASKSManagerService.smali" ]; then
    sed -i "s/ro.build.official.release/ro.build.2ndbrand/g" "$APKTOOL_DIR/system/framework/services.jar/smali/com/android/server/asks/ASKSManagerService.smali"
fi
LOG_STEP_OUT
