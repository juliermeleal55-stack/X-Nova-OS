#!/usr/bin/env bash
set -euo pipefail

system_source="${1:?stock system directory required}"
vendor_source="${2:?stock vendor directory required}"
destination="${3:?output directory required}"
search_paths=(
    "$system_source/apex/com.android.runtime/lib/bionic"
    "$system_source/apex/com.android.i18n/lib"
    "$system_source/lib"
    "$system_source/apex/com.android.vndk.current/lib"
    "$vendor_source/lib"
)
pending=(libc.so libm.so libdl.so libc++.so libhidlbase.so liblog.so libaudioproxy.so libstagefrighthw.so libExynosOMX_Core.so)
declare -A copied=()

for hardware_library in \
    "$vendor_source/bin/hw/android.hardware.audio.service" \
    "$vendor_source/lib/hw/android.hardware.audio@2.0-impl.so" \
    "$vendor_source/lib/hw/android.hardware.audio@5.0-impl.so" \
    "$vendor_source/lib/hw/android.hardware.audio@6.0-impl.so" \
    "$vendor_source/lib/hw/android.hardware.audio.effect@2.0-impl.so" \
    "$vendor_source/lib/hw/android.hardware.audio.effect@5.0-impl.so" \
    "$vendor_source/lib/hw/android.hardware.audio.effect@6.0-impl.so" \
    "$vendor_source/lib/hw/vendor.samsung.hardware.audio@1.0-impl.so" \
    "$vendor_source/lib/hw/audio.primary.exynos9820.so" \
    "$vendor_source/lib/hw/audio.primary.default.so" \
    "$vendor_source/lib/hw/android.hardware.soundtrigger@2.0-impl.so" \
    "$vendor_source/lib/hw/sound_trigger.primary.exynos9820.so" \
    "$vendor_source/bin/hw/android.hardware.media.omx@1.0-service" \
    "$vendor_source/bin/hw/vendor.samsung.hardware.camera.provider@4.0-service" \
    "$vendor_source/lib/hw/gralloc.exynos9820.so" \
    "$vendor_source"/lib/hw/camera.*.so \
    "$vendor_source"/lib/omx/*.so; do
    [[ -f "$hardware_library" ]] || continue
    while IFS= read -r dependency; do
        pending+=("$dependency")
    done < <(readelf -d "$hardware_library" | sed -n 's/.*(NEEDED).*\[\([^]]*\)\].*/\1/p')
done

mkdir -p "$destination/lib" "$destination/bin"
cp "$system_source/apex/com.android.runtime/bin/linker" "$destination/bin/s10-linker32"
for ((index = 0; index < ${#pending[@]}; index++)); do
    library="${pending[index]}"
    [[ -n "${copied[$library]:-}" ]] && continue
    resolved=""
    for search_path in "${search_paths[@]}"; do
        if [[ -f "$search_path/$library" ]]; then
            resolved="$search_path/$library"
            break
        fi
    done
    if [[ -z "$resolved" ]]; then
        printf 'Missing legacy dependency: %s\n' "$library" >&2
        exit 1
    fi
    readelf -h "$resolved" | grep -q 'Class:.*ELF32'
    cp -L "$resolved" "$destination/lib/$library"
    if readelf -d "$resolved" | grep -q '(NEEDED)'; then
        patchelf --set-rpath /vendor/lib/s10-runtime32 "$destination/lib/$library"
    fi
    copied["$library"]=1
    while IFS= read -r dependency; do
        pending+=("$dependency")
    done < <(readelf -d "$resolved" | sed -n 's/.*(NEEDED).*\[\([^]]*\)\].*/\1/p')
done
cp "$vendor_source/bin/hw/android.hardware.media.omx@1.0-service" "$destination/bin/android.hardware.media.omx@1.0-service"
patchelf --set-interpreter /vendor/bin/s10-linker32 --set-rpath /vendor/lib/s10-runtime32 \
    "$destination/bin/android.hardware.media.omx@1.0-service"
cp "$vendor_source/bin/hw/vendor.samsung.hardware.camera.provider@4.0-service" "$destination/bin/vendor.samsung.hardware.camera.provider@4.0-service"
patchelf --set-interpreter /vendor/bin/s10-linker32 --set-rpath /vendor/lib/s10-runtime32 \
    "$destination/bin/vendor.samsung.hardware.camera.provider@4.0-service"
cp "$vendor_source/bin/hw/android.hardware.audio.service" "$destination/bin/android.hardware.audio.service"
patchelf --set-interpreter /vendor/bin/s10-linker32 --set-rpath /vendor/lib/s10-runtime32 \
    "$destination/bin/android.hardware.audio.service"
helper_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$helper_directory/bind-foundation.py" \
    "$destination/lib/libstagefright_foundation.so" \
    "$destination/lib/libstagefright_foundation_vendor.so"
clang --target=armv7a-linux-androideabi31 -fPIC -fno-stack-protector -nostdlib -pie -fuse-ld=lld \
    -Wl,-e,_start -Wl,--dynamic-linker=/vendor/bin/s10-linker32 -Wl,--allow-shlib-undefined \
    -Wl,-z,max-page-size=4096 -Wl,-rpath=/vendor/lib/s10-runtime32 \
    -L"$system_source/lib" -L"$system_source/apex/com.android.runtime/lib/bionic" \
    -o "$destination/bin/s10-soundtrigger32" "$helper_directory/start.S" "$helper_directory/soundtrigger_host.c" \
    -lhidlbase -lc++ -llog -lc -ldl -lm
clang --target=aarch64-linux-android31 -DS10_BLUETOOTH_AUDIO -fPIC -fno-stack-protector -nostdlib -pie -fuse-ld=lld \
    -Wl,-e,_start -Wl,--dynamic-linker=/system/bin/linker64 -Wl,--allow-shlib-undefined \
    -Wl,-z,max-page-size=4096 \
    -L"$system_source/lib64" -L"$system_source/apex/com.android.runtime/lib64/bionic" \
    -o "$destination/bin/s10-bluetooth-audio64" "$helper_directory/start64.S" "$helper_directory/soundtrigger_host.c" \
    -lhidlbase -lc++ -llog -lc -ldl -lm
printf 'Staged %s legacy libraries\n' "${#copied[@]}"