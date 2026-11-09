#!/sbin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Recovery entrypoint: API-version output-fd ZIP-path. Candidate, not HW validated.
set -eu
(set -o pipefail) 2>/dev/null || { echo 'Recovery shell needs pipefail' >&2; exit 1; }
set -o pipefail
[ "$#" -eq 3 ] || exit 1
case "$2" in ''|*[!0-9]*) exit 1;; esac
outfd=$2
zip=$3
umask 077
log=$(mktemp /tmp/xnova-installer.XXXXXX.log) || exit 1
ui() { printf '%s\n' "$*" >> "$log"; printf 'ui_print %s\nui_print\n' "$*" > "/proc/self/fd/$outfd"; }
set_progress() { printf 'set_progress %s\n' "$1" > "/proc/self/fd/$outfd"; }
fail() { ui "ERROR $*; log=$log"; exit 1; }
for tool in cat mkdir rmdir awk tail sed unzip sha256sum dd timeout head stat df readlink mktemp mv sh sync getprop id; do
    command -v "$tool" >/dev/null 2>&1 || fail "TOOL_MISSING $tool"
done
[ "$(id -u)" = 0 ] || fail NOT_ROOT
[ "$(getprop ro.boot.em.model)" = SM-G973F ] || fail WRONG_MODEL
battery=$(cat /sys/class/power_supply/battery/capacity) || fail BATTERY_READ
case "$battery" in ''|*[!0-9]*) fail BATTERY_READ;; esac
[ "$battery" -ge 30 ] || fail BATTERY_LOW_CHARGE_FIRST
# Never stage multi-GB images on RAM/tmpfs or silently mount/decrypt userdata.
awk '$2=="/data" && ($3=="ext4" || $3=="f2fs") {ok=1} END {exit !ok}' /proc/mounts || fail DATA_NOT_MOUNTED
for path in /data /data/local /data/local/tmp; do
    [ ! -L "$path" ] || fail STAGING_SYMLINK
    [ -d "$path" ] || mkdir "$path" || fail STAGING_PARENT
 done
stage=$(mktemp -d /data/local/tmp/xnova-stage.XXXXXX) || fail STAGING_CREATE
lock=/tmp/xnova-installer.lock
mkdir "$lock" || fail ANOTHER_INSTALLER_OR_STALE_LOCK
trap 'code=$?; rmdir "$lock" 2>/dev/null || :; if [ "$code" -ne 0 ]; then ui "FAILED: preserve $log and $stage; device may be partially written if write phase started"; fi' EXIT
trap 'exit 130' INT TERM HUP
ui "X-Nova RAW installer candidate; log=$log"
# Tiny ZIP64 entry is deliberately LAST in the package, exercising large ZIP offsets.
probe=$(timeout 30 unzip -p "$zip" installer/zip64-probe.txt 2>> "$log") || fail ZIP64_UNSUPPORTED
[ "$probe" = XNOVA_RAW_V1 ] || fail ZIP64_PROBE
for entry in engine.sh manifest.tsv layout-check.sh device-base; do
    timeout 30 unzip -p "$zip" "installer/$entry" > "$stage/$entry" 2>> "$log" || fail BOOTSTRAP_EXTRACT
 done
manifest="$stage/manifest.tsv"
guard="$stage/layout-check.sh"
device_base=$(cat "$stage/device-base") || fail DEVICE_BASE
case "$device_base" in /dev/block/*) ;; *) fail DEVICE_BASE;; esac
case "$device_base" in *..*|*[!a-zA-Z0-9_./-]*) fail DEVICE_BASE;; esac
# Probe the exact dd options on private files BEFORE any target write.
printf 'self-test\n' > "$stage/tool-test"
timeout 5 dd if="$stage/tool-test" of="$stage/tool-test.out" bs=1048576 conv=notrunc,fsync >> "$log" 2>&1 || fail DD_UNSUPPORTED
test_hash=$(sha256sum "$stage/tool-test"); output_hash=$(sha256sum "$stage/tool-test.out")
[ "${test_hash%% *}" = "${output_hash%% *}" ] || fail DD_SELF_TEST
. "$stage/engine.sh"
validate_manifest
check_staging_space
check_targets
stage_images
ui 'All payloads validated. Starting non-atomic partition writes; DO NOT disconnect.'
write_images
ui "SUCCESS: all images passed readback verification. No boot validation. log=$log"
# Keep stage/logs for inspection. No recursive deletion on userdata.
