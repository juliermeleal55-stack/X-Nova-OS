TARGET_COMPAT_SOURCE="$FW_DIR/$TARGET_FIRMWARE_PATH"
TARGET_FCM_LEVEL="$(sed -n 's/.*target-level="\([^"]*\)".*/\1/p' \
    "$TARGET_COMPAT_SOURCE/vendor/etc/vintf/manifest.xml" | head -n 1)"

if [[ "$TARGET_FCM_LEVEL" != "3" ]]; then
    ABORT "Unexpected d2s target FCM level: ${TARGET_FCM_LEVEL:-missing}"
fi

for TARGET_FCM_MATRIX_LEVEL in 3 4; do
    TARGET_FCM_MATRIX="system/etc/vintf/compatibility_matrix.$TARGET_FCM_MATRIX_LEVEL.xml"
    if [ ! -f "$TARGET_COMPAT_SOURCE/system/$TARGET_FCM_MATRIX" ]; then
        ABORT "Target firmware is missing $TARGET_FCM_MATRIX"
    fi

    LOG "- Restoring d2s framework compatibility matrix level $TARGET_FCM_MATRIX_LEVEL"
    ADD_TO_WORK_DIR "$TARGET_COMPAT_SOURCE" "system" "$TARGET_FCM_MATRIX" \
        0 0 644 "u:object_r:system_file:s0"
done

# The source's Knox Matrix daemon hard-requires Samsung's modern Fkeymaster
# AIDL HAL. Exynos9825 exposes its older Keymaster implementation and cannot
# register that proprietary service. Keeping the consumer produces a permanent
# fabric_crypto abort/restart loop, so remove this self-contained unsupported
# feature and its now-untruthful framework requirement without replacing any
# boot-critical DeKnox blobs.
LOG "- Removing unsupported Knox Matrix/Fkeymaster consumers"
for KNOX_MATRIX_FILE in \
    "system/bin/fabric_crypto" \
    "system/etc/init/fabric_crypto.rc" \
    "system/etc/permissions/FabricCryptoLib.xml" \
    "system/etc/permissions/privapp-permissions-com.samsung.android.kmxservice.xml" \
    "system/etc/vintf/manifest/fabric_crypto_manifest.xml" \
    "system/framework/FabricCryptoLib.jar" \
    "system/lib64/com.samsung.security.fabric.cryptod-V1-cpp.so" \
    "system/lib64/vendor.samsung.hardware.security.fkeymaster-V1-cpp.so" \
    "system/lib64/vendor.samsung.hardware.security.fkeymaster-V1-ndk.so" \
    "system/priv-app/KmxService"
do
    DELETE_FROM_WORK_DIR "system" "$KNOX_MATRIX_FILE"
done

FKEYMASTER_MATRIX="$WORK_DIR/system/system/etc/vintf/compatibility_matrix.device.xml"
FKEYMASTER_MATRIX_COUNT="$(grep -c \
    '<name>vendor.samsung.hardware.security.fkeymaster</name>' \
    "$FKEYMASTER_MATRIX")"
if [ "$FKEYMASTER_MATRIX_COUNT" != "1" ]; then
    ABORT "Expected one framework Fkeymaster requirement, found $FKEYMASTER_MATRIX_COUNT"
fi
sed -i '/^[[:space:]]*<hal format="aidl">[[:space:]]*$/ {
    :fkeymaster_hal
    N
    /<\/hal>/!b fkeymaster_hal
    /<name>vendor\.samsung\.hardware\.security\.fkeymaster<\/name>/d
}' "$FKEYMASTER_MATRIX"

# The API 36 KnoxGuard framework and client require a modern AIDL KG provider
# and matching TEE application. Neither exists in the Exynos9825 target
# firmware. On this device the unavailable provider returns TA state Error and
# the framework fail-safe installs a remote lock despite device_locked=0. The
# accompanying SystemServer patch prevents that unsupported consumer from
# starting; remove its package and declarative references too. Keep the dormant
# multilib client libraries because they are part of the validated API 36 ABI
# snapshot and may still satisfy link-time dependencies outside KnoxGuard.
# Persistent KG state in /data and every hardware-backed security partition are
# deliberately left untouched.
LOG "- Removing unsupported Android 16 KnoxGuard consumer"
for KNOX_GUARD_FILE in \
    "system/etc/permissions/privapp-permissions-com.samsung.android.kgclient.xml" \
    "system/etc/permissions/signature-permissions-com.samsung.android.kgclient.xml" \
    "system/priv-app/KnoxGuard"
do
    DELETE_FROM_WORK_DIR "system" "$KNOX_GUARD_FILE"
done

KNOX_GUARD_MATRIX_COUNT="$(grep -c \
    '<name>vendor.samsung.hardware.tlc.kg</name>' \
    "$FKEYMASTER_MATRIX")"
if [ "$KNOX_GUARD_MATRIX_COUNT" != "1" ]; then
    ABORT "Expected one framework KnoxGuard requirement, found $KNOX_GUARD_MATRIX_COUNT"
fi
sed -i \
    -e '/vendor\/samsung\/interfaces\/tlc\/kg\/2\.0\/aidl\/vendor\.samsung\.hardware\.tlc\.kg-matrix\.xml/d' \
    -e '/^[[:space:]]*<hal format="aidl">[[:space:]]*$/ {
        :knoxguard_hal
        N
        /<\/hal>/!b knoxguard_hal
        /<name>vendor\.samsung\.hardware\.tlc\.kg<\/name>/d
    }' \
    "$FKEYMASTER_MATRIX"

KNOX_GUARD_CONFIGS=(
    "system/etc/broadcast_allowlist.xml"
    "system/etc/deviceidle/reviewed_allowlist.xml"
    "system/etc/irremovable_list.txt"
    "system/etc/permissions/platform.xml"
    "system/etc/sysconfig/allowed-system-preload-apps.xml"
    "system/etc/sysconfig/system-required-packages.xml"
    "system/etc/sysconfig/safe-mode-allow-list.xml"
)
for KNOX_GUARD_CONFIG in "${KNOX_GUARD_CONFIGS[@]}"; do
    KNOX_GUARD_CONFIG_PATH="$WORK_DIR/system/$KNOX_GUARD_CONFIG"
    if [ ! -f "$KNOX_GUARD_CONFIG_PATH" ]; then
        ABORT "KnoxGuard declarative config is missing: $KNOX_GUARD_CONFIG"
    fi
    KNOX_GUARD_CONFIG_COUNT="$(grep -c 'com.samsung.android.kgclient' \
        "$KNOX_GUARD_CONFIG_PATH")"
    if [ "$KNOX_GUARD_CONFIG_COUNT" -lt 1 ]; then
        ABORT "Expected KnoxGuard reference in $KNOX_GUARD_CONFIG"
    fi
    sed -i '/com\.samsung\.android\.kgclient/d' "$KNOX_GUARD_CONFIG_PATH"
done

# One UI 9 (API 37) ships a dedicated preinstalled-packages file for KnoxGuard; the
# package itself is removed above, so drop the leftover declaration too.
rm -f "$WORK_DIR/system/system/etc/sysconfig/preinstalled-packages-com.samsung.android.kgclient.xml"

# Secure Folder must not key its availability to the obsolete ICCC property.
# The d2s services.jar patch below handles the actual SAK/DRK results while
# keeping KnoxGuard and every hardware-backed security partition untouched.
SET_PROP "system" "ro.config.iccc_version" --delete

# Current Android releases keep generated Aconfig maps below /metadata. The
# Exynos9825 partition layout predates that partition, leaving the read-only
# system-root mount point as the only /metadata path. Supply a small ephemeral
# backing store before aconfigd's own early-init action. The maps are rebuilt
# from signed system/APEX inputs on every boot, so persistence is unnecessary;
# /data and every user file remain untouched.
ACONFIG_INIT_RC="$WORK_DIR/system/system/etc/init/aconfigd.rc"
ACONFIG_EARLY_INIT_COUNT="$(grep -c '^on early-init$' "$ACONFIG_INIT_RC")"
if [ "$ACONFIG_EARLY_INIT_COUNT" != "1" ]; then
    ABORT "Expected one Aconfig early-init action, found $ACONFIG_EARLY_INIT_COUNT"
fi
sed -i '/^on early-init$/a\
    # d2s: emulate the missing modern metadata partition for generated flags.\
    mount tmpfs tmpfs /metadata nodev noexec nosuid mode=0775,uid=0,gid=1000,size=64m' \
    "$ACONFIG_INIT_RC"

# The API 33 vendor adaptation adds the AIDL health service needed by current
# framework code, but it also deleted the truthful HIDL 2.1 service required by
# the d2s FCM3 contract. The two binder interfaces have different formats and
# can coexist; retain both instead of weakening or falsifying the matrix.
LOG "- Restoring the d2s HIDL health compatibility service"
for TARGET_HEALTH_FILE in \
    "bin/hw/android.hardware.health@2.1-service-samsung" \
    "etc/init/android.hardware.health@2.1-service-samsung.rc" \
    "etc/vintf/manifest/android.hardware.health@2.1-samsung.xml" \
    "lib/android.hardware.health@2.1.so" \
    "lib64/android.hardware.health@2.1.so"
do
    ADD_TO_WORK_DIR "$TARGET_COMPAT_SOURCE" "vendor" "$TARGET_HEALTH_FILE"
done

# One UI 8.5/API 36 libaudiohal no longer ships a HIDL 5.0 client adapter. The
# d2s vendor manifest and passthrough implementations were still 5.0, so
# audioserver could not create either IDevicesFactory or IEffectsFactory. Keep
# the device-specific Exynos9825 legacy C HAL, mixer and effects untouched, but
# expose them through the generic Android 12/VNDK31 HIDL 6.0 wrappers from the
# same multilib firmware that supplies this build's 32-bit runtime.
LOG_STEP_IN "- Installing the d2s HIDL audio 6.0 compatibility bridge"
if [ -z "${MULTILIB_FIRMWARE:-}" ]; then
    ABORT "MULTILIB_FIRMWARE is required for the d2s audio bridge"
fi

AUDIO_BRIDGE_SOURCE="$FW_DIR/$(cut -d "/" -f 1 -s <<< "$MULTILIB_FIRMWARE")_$(cut -d "/" -f 2 -s <<< "$MULTILIB_FIRMWARE")"
AUDIO_BRIDGE_MARKER="S711BXXSGGZF2/S711BOXMGGZF2/S711BXXSGGZF2"
if [ "$(cat "$AUDIO_BRIDGE_SOURCE/.extracted" 2> /dev/null)" != \
        "$AUDIO_BRIDGE_MARKER" ]; then
    ABORT "Unexpected d2s audio bridge firmware in $AUDIO_BRIDGE_SOURCE"
fi

while read -r AUDIO_BRIDGE_SHA256 AUDIO_BRIDGE_FILE; do
    [ -n "$AUDIO_BRIDGE_FILE" ] || continue
    AUDIO_BRIDGE_INPUT="$AUDIO_BRIDGE_SOURCE/vendor/$AUDIO_BRIDGE_FILE"
    if [ ! -f "$AUDIO_BRIDGE_INPUT" ]; then
        ABORT "Audio bridge input is missing: $AUDIO_BRIDGE_INPUT"
    fi
    if [ "$(sha256sum "$AUDIO_BRIDGE_INPUT" | cut -d " " -f 1)" != \
            "$AUDIO_BRIDGE_SHA256" ]; then
        ABORT "Audio bridge input hash changed: $AUDIO_BRIDGE_FILE"
    fi

    ADD_TO_WORK_DIR "$AUDIO_BRIDGE_SOURCE" "vendor" "$AUDIO_BRIDGE_FILE" || \
        ABORT "Failed to install audio bridge file: $AUDIO_BRIDGE_FILE"
    if [ "$(sha256sum "$WORK_DIR/vendor/$AUDIO_BRIDGE_FILE" | cut -d " " -f 1)" != \
            "$AUDIO_BRIDGE_SHA256" ]; then
        ABORT "Installed audio bridge hash mismatch: $AUDIO_BRIDGE_FILE"
    fi
done <<'EOF'
57092f6b3e4af8877d4e23bd32aea197f3b5df9bb7c61f74d3ce3f99ca16aeef lib/hw/android.hardware.audio@6.0-impl.so
0c76d753d51005140b6d029923a53ab8c3b0a559c5536288ddecfd45f3ba275b lib/hw/android.hardware.audio.effect@6.0-impl.so
109bfdee3c58e6b7d297523aeb4b71b4d6782be843855c21aa6da191b1c50e20 lib/android.hardware.audio.common@6.0.so
73cf8256fb62e128cd47b3e1ae2c5013c6c0ca6c4495ac3b93d22476a1de8606 lib/android.hardware.audio.common@6.0-util.so
1f336b8025d87ff702d489d35c4fac1468263530b90102af74e3c713c35656c5 lib/android.hardware.audio@6.0.so
53a08a73458bfc64a0612f8e4fcd4cf63d91121872da1238c8ceb9b726ddf4d5 lib/android.hardware.audio@6.0-util.so
1c8fef364f95e9142ff0f43ab1f76a8278fcd17752383a36765f2d62e0e5ceb1 lib/android.hardware.audio.effect@6.0.so
e606e14965234e9e81d761a530b4b8ccacc66853d029087fce9a93f70de00f6a lib/android.hardware.audio.effect@6.0-util.so
8a34942d275bc565cdbd811755cc15aaa7fc8d75f891678fe2db10378644054e lib/soundfx/libswspatializer.so
444f4f4bf395eed954eab0f7a6396be1e34a0884a6ceccd0efe337cf1899d15f lib/spatializer-aidl-cpp.so
b5bf81305153f730f34f99e3162511817c66ac491ba760c9f06d80c23c56b798 lib64/soundfx/libswspatializer.so
57b159e54bdba0727617481ad891933a51090d0325aefe5c0e7e657d10f6d633 lib64/spatializer-aidl-cpp.so
EOF

AUDIO_MANIFEST="$WORK_DIR/vendor/etc/vintf/manifest.xml"
sed -i \
    -e '/<name>android.hardware.audio<\/name>/,/<\/hal>/ { s/<version>5\.0<\/version>/<version>6.0<\/version>/; s/@5\.0::IDevicesFactory/@6.0::IDevicesFactory/; }' \
    -e '/<name>android.hardware.audio.effect<\/name>/,/<\/hal>/ { s/<version>5\.0<\/version>/<version>6.0<\/version>/; s/@5\.0::IEffectsFactory/@6.0::IEffectsFactory/; }' \
    "$AUDIO_MANIFEST"
LOG_STEP_OUT

# Android 16 25Q4's Tethering APEX refuses every kernel older than 5.10 before
# it attempts to load a single BPF object. The d2s kernel exposes the backported
# network-BPF baseline as 5.4.186, so the hard gate reboots with status 7 even
# though all earlier Android U and Q2 gates pass. Keep the reported version
# truthful for the loader's later per-object compatibility decisions and bypass
# only the new unconditional 25Q4 refusal.
#
# Modifying the compressed APEX would invalidate both of its signatures. Extract
# its complete bin directory into /system instead, patch one exact instruction,
# and bind-mount that directory over the original after APEXd has activated it.
# Executing through the original /apex path preserves the Tethering linker
# namespace. All inputs and the one output are hash-pinned so source drift fails
# the build rather than silently producing an unsafe patch.
LOG_STEP_IN "- Installing the d2s Android 16 NetBpfLoad compatibility layer"
BPF_APEX="$WORK_DIR/system/system/apex/com.google.android.tethering_compressed.apex"
BPF_COMPAT_ROOT="$WORK_DIR/system/system/etc/netbpfload_compat"
BPF_COMPAT_BIN="$BPF_COMPAT_ROOT/bin"
mkdir -p "$TMP_DIR"
BPF_TMP_ROOT="$(mktemp -d "$TMP_DIR/netbpfload-compat.XXXXXX")"

if [ ! -f "$BPF_APEX" ]; then
    ABORT "Tethering compressed APEX is missing: $BPF_APEX"
fi
if ! command -v debugfs > /dev/null; then
    ABORT "debugfs is required to extract the Tethering APEX payload"
fi

mkdir -p "$BPF_COMPAT_BIN/for-system"
EVAL "unzip -j \"$BPF_APEX\" original_apex -d \"$BPF_TMP_ROOT\""
EVAL "unzip -j \"$BPF_TMP_ROOT/original_apex\" apex_payload.img -d \"$BPF_TMP_ROOT\""

while read -r BPF_INPUT_SHA256 BPF_INPUT_PATH BPF_INPUT_UID \
        BPF_INPUT_GID BPF_INPUT_MODE BPF_INPUT_LABEL; do
    [ -n "$BPF_INPUT_PATH" ] || continue
    BPF_OUTPUT="$BPF_COMPAT_BIN/$BPF_INPUT_PATH"
    EVAL "debugfs -R \"dump -p /bin/$BPF_INPUT_PATH $BPF_OUTPUT\" \"$BPF_TMP_ROOT/apex_payload.img\""
    if [ "$(sha256sum "$BPF_OUTPUT" | cut -d " " -f 1)" != \
            "$BPF_INPUT_SHA256" ]; then
        ABORT "Tethering APEX input hash changed: /bin/$BPF_INPUT_PATH"
    fi
    SET_METADATA "system" "system/etc/netbpfload_compat/bin/$BPF_INPUT_PATH" \
        "$BPF_INPUT_UID" "$BPF_INPUT_GID" "$BPF_INPUT_MODE" \
        "$BPF_INPUT_LABEL"
done <<'EOF'
94e002a189db9f0f605c1c80cdc969b5c7b0a25c72be9ed39c00cf6cb885fc4b ethtool 0 2000 755 u:object_r:system_file:s0
60afc10c53d7ffd2bc056d2f3ce7a8e16848b53b53a0126870318369844d1b63 for-system/clatd 1029 1029 6755 u:object_r:clatd_exec:s0
775d705134ac47146a536d31e76af3d439d0e29d48087bc6c64d04c102c4bed6 netbpfload 0 0 750 u:object_r:bpfloader_exec:s0
68fbcf063b5cb5653d1636d0cf85b896a7d3e6a842c437df890558e8377edfcc ot-daemon 0 2000 755 u:object_r:ot_daemon_exec:s0
EOF

SET_METADATA "system" "system/etc/netbpfload_compat" \
    0 2000 755 "u:object_r:system_file:s0"
SET_METADATA "system" "system/etc/netbpfload_compat/bin" \
    0 2000 755 "u:object_r:system_file:s0"
SET_METADATA "system" "system/etc/netbpfload_compat/bin/for-system" \
    1029 1000 750 "u:object_r:system_file:s0"

BPF_LOADER="$BPF_COMPAT_BIN/netbpfload"
# API 37 NetBpfLoad refuses kernels below 5.10 (25Q4) and 5.15 (26Q3) once the
# platform API level reaches 36.1/37.1. ExtremeKRNL reports a 5.4 network-BPF
# baseline, so clear only these two release flags at their gate sites:
# "ldrb wN, [xN, #flag]" becomes "mov wN, #0" and the following tbz takes the
# normal pass path with the same register state as on an older platform.
# Android 17 also aborts when a BPF object is not on the loader's filesystem,
# which the bind mount below always causes, so drop that branch. And netd needs
# prog_netd_egress_stats, whose 5.4 variant only exists for API < 36.1: compare
# program API ranges against 36.0, not 37 (mov w4, #3600).
for BPF_GATE in \
        "6a0800d04a914439ca000036 6a0800d00a008052ca000036" \
        "680800d008a1443928010036 680800d00800805228010036" \
        "9f0005eb41210054 9f0005eb1f2003d5" \
        "259b432904f540b99f00056b 259b432904c281529f00056b"; do
    BPF_FROM="${BPF_GATE% *}"
    BPF_TO="${BPF_GATE#* }"
    BPF_MATCH_COUNT="$(xxd -p "$BPF_LOADER" | tr -d ' \n' | grep -o "$BPF_FROM" | wc -l)"
    if [ "$BPF_MATCH_COUNT" != "1" ]; then
        ABORT "Expected one API 37 NetBpfLoad kernel gate $BPF_FROM, found $BPF_MATCH_COUNT"
    fi
    HEX_PATCH "$BPF_LOADER" "$BPF_FROM" "$BPF_TO" || \
        ABORT "Failed to patch the API 37 NetBpfLoad kernel gate $BPF_FROM"
done
if [ "$(sha256sum "$BPF_LOADER" | cut -d " " -f 1)" != \
        "51cb5af47750ea62caf69062123adcdfd6c4663afea4b4e50a799ec64c761118" ]; then
    ABORT "Patched NetBpfLoad hash mismatch"
fi

# ConnectivityService aborts system_server when two BPF ring buffers are missing,
# and they need kernel 5.8+. Local network access metrics now poll /dev/null via a
# dup of fd 0, and the loopback event poller never starts.
BPF_COMPAT_LIB="$BPF_COMPAT_ROOT/lib64"
BPF_CONNECTIVITY="$BPF_COMPAT_LIB/libservice-connectivity.so"
mkdir -p "$BPF_COMPAT_LIB"
EVAL "debugfs -R \"dump -p /lib64/libservice-connectivity.so $BPF_CONNECTIVITY\" \"$BPF_TMP_ROOT/apex_payload.img\""
if [ "$(sha256sum "$BPF_CONNECTIVITY" | cut -d " " -f 1)" != \
        "7e23e345bb832ccda5ff0b1b2dfe6d5bab243e82b1451d5285f8806a11159382" ]; then
    ABORT "Tethering APEX input hash changed: /lib64/libservice-connectivity.so"
fi
HEX_PATCH "$BPF_CONNECTIVITY" "f21b0094001840b9c1808052" "1f2003d5e0031f2ac1808052" || \
    ABORT "Failed to patch nativeGetLocalNetAccessRingbufFd"
HEX_PATCH "$BPF_CONNECTIVITY" "3f2303d5ff4301d1fd7b02a9f51b00f9f44f04a9fd83009155d03bd5530000d0" "c0035fd6ff4301d1fd7b02a9f51b00f9f44f04a9fd83009155d03bd5530000d0" || \
    ABORT "Failed to patch LoopbackEventHandler::Start"
HEX_PATCH "$BPF_CONNECTIVITY" "3f2303d5fd7bbfa9fd0300911f2003d568f60410" "c0035fd6fd7bbfa9fd0300911f2003d568f60410" || \
    ABORT "Failed to patch LoopbackEventHandler::Stop"
if [ "$(sha256sum "$BPF_CONNECTIVITY" | cut -d " " -f 1)" != \
        "15f6410c48617e957f5c9902f96c0dff9d49763fb4598f656c145c6247af28d9" ]; then
    ABORT "Patched libservice-connectivity hash mismatch"
fi
SET_METADATA "system" "system/etc/netbpfload_compat/lib64" \
    0 2000 755 "u:object_r:system_file:s0"
SET_METADATA "system" "system/etc/netbpfload_compat/lib64/libservice-connectivity.so" \
    0 0 644 "u:object_r:system_lib_file:s0"
# The policy lets init bind over directories only; this bind targets a file.
echo "(allow init system_lib_file (file (mounton)))" >> "$WORK_DIR/system/system/etc/selinux/plat_sepolicy.cil"

BPF_INIT_RC="$WORK_DIR/system/system/etc/init/netbpfload.rc"
BPF_TRIGGER_COUNT="$(grep -c '^[[:space:]]*exec_start bpfloader[[:space:]]*$' "$BPF_INIT_RC")"
if [ "$BPF_TRIGGER_COUNT" != "1" ]; then
    ABORT "Expected one load-bpf-programs bpfloader start, found $BPF_TRIGGER_COUNT"
fi
sed -i '/^[[:space:]]*exec_start bpfloader[[:space:]]*$/i\
    # d2s: retain the APEX path/namespace while bypassing only its 5.10/5.15 hard gates.\
    mount none /system/etc/netbpfload_compat/lib64/libservice-connectivity.so /apex/com.android.tethering/lib64/libservice-connectivity.so bind\
    mount none /system/etc/netbpfload_compat/bin /apex/com.android.tethering/bin bind' \
    "$BPF_INIT_RC"

rm -f "$BPF_TMP_ROOT/original_apex" "$BPF_TMP_ROOT/apex_payload.img"
rmdir "$BPF_TMP_ROOT"
LOG_STEP_OUT

LOG "- Updating legacy d2s ueventd sysfs rules"
sed -i \
    -e 's|^/sys/kernel/clat/xlat_v4_addrs[[:space:]].*|/sys/kernel/clat xlat_v4_addrs 0660 clat clat|' \
    -e 's|^/sys/kernel/clat/xlat_addrs[[:space:]].*|/sys/kernel/clat xlat_addrs 0660 clat clat|' \
    -e 's|^/sys/kernel/clat/xlat_plat[[:space:]].*|/sys/kernel/clat xlat_plat 0660 clat clat|' \
    -e '/^\/sys\/bus\/iio\/devices\/iio:device\*[[:space:]][[:space:]]*0664[[:space:]][[:space:]]*system[[:space:]][[:space:]]*radio[[:space:]]*$/d' \
    "$WORK_DIR/vendor/ueventd.rc"

# Android 17 removed /dev/ion from its contexts and the gralloc 2.x/3.x mapper
# fallback from libui (api > 35 gates). The d2s vendor only has mapper 2.0 on ION.
LOG_STEP_IN "- Restoring ION and the gralloc 2.x mapper"
echo "/dev/ion u:object_r:ion_device:s0" >> "$WORK_DIR/system/system/etc/selinux/plat_file_contexts"
LIBUI="$WORK_DIR/system/system/lib64/libui.so"
if [ "$(sha256sum "$LIBUI" | cut -d " " -f 1)" != \
        "4bc342521a9745c3c5fa7b8bc9987e8437a043ef16bfb4a2e1f98ec6ecbf0122" ]; then
    ABORT "libui.so input hash changed"
fi
HEX_PATCH "$LIBUI" "8bbc00941f8c0071ac030054" "8bbc00941f8c00711f2003d5" || ABORT "Failed to patch GraphicBufferMapper"
HEX_PATCH "$LIBUI" "9cb900941f8c0071ac050054" "9cb900941f8c00711f2003d5" || ABORT "Failed to patch GraphicBuffer"
HEX_PATCH "$LIBUI" "9a2400941f8c00716c000054" "9a2400941f8c00711f2003d5" || ABORT "Failed to patch GraphicBufferMapper::preloadHal"
if [ "$(sha256sum "$LIBUI" | cut -d " " -f 1)" != \
        "ef711d73fea58a7b234ff35cf66e2ef8b7bfae37cd8923d8adf8cf751e0bb606" ]; then
    ABORT "Patched libui.so hash mismatch"
fi
unset LIBUI
LOG_STEP_OUT

# SDHMS decrypts its thermal policy with SHA-256(SIOP_POLICY_FILENAME). The donor's
# assets only decrypt under the S24 FE name, whose policy crash-loops SDHMS here, so
# the Note10+ name yields garbage and the "Fails to parse DEFAULT policy XML" warning.
# Ship the stock Note10+ policies under the Note10+ key instead.
LOG_STEP_IN "- Installing the stock Note10+ thermal policy"
SDHMS_APK="$WORK_DIR/system/system/priv-app/SamsungDeviceHealthManagerService/SamsungDeviceHealthManagerService.apk"
SDHMS_STOCK_APK="$FW_DIR/$(cut -d "/" -f 1,2 <<< "$TARGET_FIRMWARE" | tr "/" "_")/system/system/priv-app/SamsungDeviceHealthManagerService/SamsungDeviceHealthManagerService.apk"
SDHMS_KEY="$(printf '%s' siop_davinci2_exynos9820 | sha256sum | cut -d " " -f 1)"
SDHMS_TMP="$(mktemp -d "$TMP_DIR/sdhms-policy.XXXXXX")"
mkdir -p "$SDHMS_TMP/assets"
EVAL "unzip -j \"$SDHMS_STOCK_APK\" res/raw/siop_default.xml res/raw/siop_davinci2_exynos9820.xml -d \"$SDHMS_TMP\""
# The Android 17 parser aborts on overheat types it no longer knows.
sed -i '/<DEX /d' "$SDHMS_TMP/siop_default.xml"
for SDHMS_POLICY in "siop_default siop_default.xml" "siop_model siop_davinci2_exynos9820.xml"; do
    SDHMS_ASSET="${SDHMS_POLICY% *}"
    SDHMS_SOURCE="${SDHMS_POLICY#* }"
    SDHMS_IV="$(openssl rand -hex 16)"
    xxd -r -p <<< "$SDHMS_IV" > "$SDHMS_TMP/assets/$SDHMS_ASSET"
    openssl enc -aes-256-cbc -K "$SDHMS_KEY" -iv "$SDHMS_IV" -in "$SDHMS_TMP/$SDHMS_SOURCE" >> "$SDHMS_TMP/assets/$SDHMS_ASSET" || \
        ABORT "Failed to encrypt $SDHMS_SOURCE"
done
(cd "$SDHMS_TMP" && zip -q -X -0 "$SDHMS_APK" assets/siop_default assets/siop_model) || \
    ABORT "Failed to replace the SDHMS policy assets"
CERT_PREFIX="aosp"
$ROM_IS_OFFICIAL && CERT_PREFIX="impulse"
EVAL "signapk \"$SRC_DIR/security/${CERT_PREFIX}_platform.x509.pem\" \"$SRC_DIR/security/${CERT_PREFIX}_platform.pk8\" \"$SDHMS_APK\" \"$SDHMS_TMP/signed.apk\"" || \
    ABORT "Failed to sign SDHMS"
mv -f "$SDHMS_TMP/signed.apk" "$SDHMS_APK"
rm -rf "$SDHMS_TMP"
unset SDHMS_APK SDHMS_STOCK_APK SDHMS_KEY SDHMS_TMP SDHMS_POLICY SDHMS_ASSET SDHMS_SOURCE SDHMS_IV CERT_PREFIX
LOG_STEP_OUT

unset TARGET_COMPAT_SOURCE TARGET_FCM_LEVEL TARGET_FCM_MATRIX
unset TARGET_FCM_MATRIX_LEVEL TARGET_HEALTH_FILE
unset KNOX_MATRIX_FILE FKEYMASTER_MATRIX FKEYMASTER_MATRIX_COUNT
unset KNOX_GUARD_FILE KNOX_GUARD_MATRIX_COUNT
unset KNOX_GUARD_CONFIG KNOX_GUARD_CONFIGS KNOX_GUARD_CONFIG_PATH
unset KNOX_GUARD_CONFIG_COUNT
unset ACONFIG_INIT_RC ACONFIG_EARLY_INIT_COUNT
unset AUDIO_BRIDGE_SOURCE AUDIO_BRIDGE_MARKER AUDIO_BRIDGE_SHA256
unset AUDIO_BRIDGE_FILE AUDIO_BRIDGE_INPUT AUDIO_MANIFEST
unset BPF_APEX BPF_COMPAT_ROOT BPF_COMPAT_BIN BPF_TMP_ROOT
unset BPF_INPUT_SHA256 BPF_INPUT_PATH BPF_INPUT_UID BPF_INPUT_GID
unset BPF_INPUT_MODE BPF_INPUT_LABEL BPF_OUTPUT
unset BPF_LOADER BPF_GATE BPF_FROM BPF_TO BPF_MATCH_COUNT
unset BPF_INIT_RC BPF_TRIGGER_COUNT
