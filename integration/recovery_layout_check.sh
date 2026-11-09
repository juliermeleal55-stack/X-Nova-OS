# SPDX-License-Identifier: GPL-3.0-or-later
# Read-only recovery helper. Generated callers supply only validated names/bytes.
base=${1:-/dev/block/by-name}
LOG=${PARTITION_CHECK_LOG:-/tmp/partition-layout-check.log}
: > "$LOG" || exit 1
log()
{
    printf '%s\n' "$*" >> "$LOG"
    printf '%s\n' "$*"
}
is_block() { [ -b "$1" ]; }
is_decimal()
{
    case "$1" in ''|*[!0-9]*) return 1;; esac
}
# Compare decimal strings without overflowing 32-bit recovery shell integers.
decimal_ge()
{
    left=$1; right=$2
    while [ "${left#0}" != "$left" ]; do left=${left#0}; done
    while [ "${right#0}" != "$right" ]; do right=${right#0}; done
    left=${left:-0}; right=${right:-0}
    [ "${#left}" -gt "${#right}" ] && return 0
    [ "${#left}" -lt "${#right}" ] && return 1
    while [ -n "$left" ]; do
        l=${left%"${left#?}"}; r=${right%"${right#?}"}
        [ "$l" -gt "$r" ] && return 0
        [ "$l" -lt "$r" ] && return 1
        left=${left#?}; right=${right#?}
    done
    return 0
}
read_capacity()
{
    size=; reader=
    for tool in blockdev busybox toybox; do
        if [ "$tool" = blockdev ]; then
            candidate=$(blockdev --getsize64 "$part" 2>> "$LOG") || continue
        else
            candidate=$("$tool" blockdev --getsize64 "$part" 2>> "$LOG") || continue
        fi
        is_decimal "$candidate" || continue
        decimal_ge "$candidate" 1 || continue
        size=$candidate; reader=$tool; return 0
    done
    # sysfs reports 512-byte sectors, regardless of the device's logical block size.
    resolved=$(readlink -f "$part" 2>> "$LOG") || return 1
    [ -n "$resolved" ] || return 1
    sectors=$(cat "/sys/class/block/${resolved##*/}/size" 2>> "$LOG") || return 1
    is_decimal "$sectors" || return 1
    candidate=$(printf '%s\n' "$sectors" | awk '{printf "%.0f\n", $1 * 512}' 2>> "$LOG") || return 1
    is_decimal "$candidate" || return 1
    decimal_ge "$candidate" 1 || return 1
    size=$candidate; reader=sysfs; return 0
}
mount_table() { cat /proc/mounts; }
mount_source_matches()
{
    [ -b "$1" ] || return 1
    mounted_device=$(readlink -f "$1") || return 2
    target_device=$(readlink -f "$part") || return 2
    [ -n "$mounted_device" ] && [ "$mounted_device" = "$target_device" ]
}
partition_is_unmounted()
{
    mounts=$(mount_table) || return 2
    [ -n "$mounts" ] || return 2
    while read -r source mountpoint remainder; do
        if mount_source_matches "$source"; then
            log "ERR_MOUNTED partition=$name path=$part mountpoint=$mountpoint"
            log 'Target still mounted. Unmount it in recovery before installing; no writes permitted.'
            return 1
        else
            match_status=$?
            [ "$match_status" -ne 2 ] || return 2
        fi
    done <<MOUNTS
$mounts
MOUNTS
    return 0
}
check_partition()
{
    name=$1; required=$2; part="$base/$name"
    if ! is_block "$part"; then
        log "ERR_MISSING partition=$name path=$part required_bytes=$required"
        log 'Configured write target is absent. Verify recovery paths; this is NOT proof of insufficient space.'
        return 1
    fi
    if ! read_capacity; then
        log "ERR_READ partition=$name path=$part required_bytes=$required"
        log 'Cannot obtain capacity with blockdev/busybox/toybox/sysfs. This is NOT proof of insufficient space.'
        return 1
    fi
    if ! decimal_ge "$size" "$required"; then
        log "ERR_TOO_SMALL partition=$name path=$part actual_bytes=$size required_bytes=$required reader=$reader"
        return 1
    fi
    partition_is_unmounted
    mounted_status=$?
    if [ "$mounted_status" -ne 0 ]; then
        [ "$mounted_status" -ne 2 ] || log "ERR_MOUNT_READ partition=$name: cannot read mount table"
        return 1
    fi
    log "OK partition=$name path=$part actual_bytes=$size required_bytes=$required reader=$reader"
}
log "Read-only partition check: configured write base=$base"
failures=0
