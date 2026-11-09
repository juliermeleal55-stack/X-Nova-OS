# SPDX-License-Identifier: GPL-3.0-or-later
# X-Nova raw-v1 engine. No automatic mounts, formats, resize or repartition.
# Caller supplies validated private paths and UI functions. No test-mode bypass.
abort() { ui "ERROR $*"; exit 1; }
validate_manifest()
{
    seen=' '
    image_count=0
    while read -r name bytes digest extra; do
        case "$name" in system|vendor|product|odm|prism|optics|system_ext|dtbo|boot) ;; *) abort MANIFEST_NAME;; esac
        case "$seen" in *" $name "*) abort MANIFEST_DUPLICATE;; esac
        seen="$seen$name "
        case "$bytes" in ''|0*|*[!0-9]*) abort MANIFEST_SIZE;; esac
        # Exact integer arithmetic in awk up to 2^53; not a device size ceiling.
        [ "${#bytes}" -le 16 ] || abort MANIFEST_SIZE_RANGE
        awk -v n="$bytes" 'BEGIN {exit !(n < 9007199254740992)}' || abort MANIFEST_SIZE_RANGE
        case "$digest" in *[!a-f0-9]*) abort MANIFEST_HASH;; esac
        [ "${#digest}" -eq 64 ] && [ -z "$extra" ] || abort MANIFEST_FIELDS
        image_count=$((image_count + 1))
    done < "$manifest"
    for required in system vendor product dtbo boot; do
        case "$seen" in *" $required "*) ;; *) abort MANIFEST_REQUIRED;; esac
    done
    # Boot is written last. Reject a reordered manifest rather than infer intent.
    [ "$(tail -n 1 "$manifest" | awk '{print $1}')" = boot ] || abort MANIFEST_BOOT_ORDER
}
check_staging_space()
{
    available=$(df -Pk "$stage" | awk 'NR==2 {printf "%.0f", $4 * 1024}')
    case "$available" in ''|*[!0-9]*) abort STAGING_SPACE_READ;; esac
    awk -v free="$available" '{total += $2} END {exit !(free >= total + 67108864)}' "$manifest" || abort STAGING_SPACE_SMALL
}
check_targets()
(
    # The existing read-only guard checks ALL capacities/mounts before any write.
    PARTITION_CHECK_LOG="$stage/layout.log" sh "$guard" "$device_base" >> "$log" 2>&1 || abort TARGET_GUARD
    resolved_seen=' '
    while read -r name bytes digest extra; do
        device=$(readlink -f "$device_base/$name") || abort TARGET_RESOLVE
        [ -b "$device" ] || abort TARGET_NOT_BLOCK
        case "$resolved_seen" in *" $device "*) abort TARGET_ALIAS_COLLISION;; esac
        resolved_seen="$resolved_seen$device "
    done < "$manifest"
)
stage_images()
{
    while read -r name bytes digest extra; do
        ui "Validating $name before any device write"
        timeout 1800 unzip -p "$zip" "images/$name.img" > "$stage/$name.partial" 2>> "$log" || abort STAGE_EXTRACT
        actual=$(stat -c %s "$stage/$name.partial") || abort STAGE_STAT
        [ "$actual" = "$bytes" ] || abort STAGE_SIZE
        actual_hash=$(sha256sum "$stage/$name.partial") || abort STAGE_HASH_READ
        [ "${actual_hash%% *}" = "$digest" ] || abort STAGE_HASH_MISMATCH
        mv "$stage/$name.partial" "$stage/$name.img" || abort STAGE_RENAME
    done < "$manifest"
}
write_one()
{
    name=$1; bytes=$2; digest=$3
    target="$device_base/$name"
    blocks=$(awk -v n="$bytes" 'BEGIN {printf "%.0f", int((n + 1048575)/1048576)}')
    # Chunk offsets must fit recovery shell integer arithmetic.
    awk -v n="$blocks" 'BEGIN {exit !(n <= 2147483647)}' || abort WRITE_OFFSET_RANGE
    done_blocks=0
    while [ "$done_blocks" -lt "$blocks" ]; do
        remaining=$((blocks - done_blocks))
        chunk=32
        [ "$remaining" -ge 32 ] || chunk=$remaining
        ui "Writing $name: next chunk from MiB block $done_blocks (timeout 180s)"
        if timeout 180 dd if="$stage/$name.img" of="$target" bs=1048576 count="$chunk" skip="$done_blocks" seek="$done_blocks" conv=notrunc,fsync >> "$log" 2>&1; then
            :
        else
            code=$?
            abort "WRITE_CHUNK partition=$name exit=$code (124 means timeout)"
        fi
        done_blocks=$((done_blocks + chunk))
        ui "$name: completed $done_blocks/$blocks MiB blocks"
        progress=$(awk -v i="$image_index" -v n="$image_count" -v p="$done_blocks" -v total="$blocks" 'BEGIN {printf "%.6f", (i-1+0.9*p/total)/n}')
        set_progress "$progress"
    done
    ui "Readback verification: $name"
    actual_hash=$(timeout 900 head -c "$bytes" "$target" | sha256sum) || abort READBACK_IO
    [ "${actual_hash%% *}" = "$digest" ] || abort READBACK_HASH_MISMATCH
    ui "Verified on target: $name"
    progress=$(awk -v i="$image_index" -v n="$image_count" 'BEGIN {printf "%.6f", i/n}')
    set_progress "$progress"
}
write_images()
{
    image_index=0
    while read -r name bytes digest extra; do
        # Recheck mounts/capacity immediately before each partition write.
        check_targets || abort TARGET_RECHECK
        image_index=$((image_index + 1))
        write_one "$name" "$bytes" "$digest"
    done < "$manifest"
    sync || abort SYNC
}
