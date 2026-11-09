#!/sbin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Optional standalone capability probe. No block writes, mounts or formatting.
set -u
printf 'XNOVA_RAW_RECOVERY_PROBE_V1\n'
for tool in unzip sha256sum dd timeout head stat df awk readlink mktemp getprop; do
    if command -v "$tool" >/dev/null 2>&1; then
        printf 'tool_%s=available\n' "$tool"
    else
        printf 'tool_%s=MISSING\n' "$tool"
    fi
done
if (set -o pipefail) 2>/dev/null; then printf 'pipefail=available\n'; else printf 'pipefail=MISSING\n'; fi
printf 'model=%s\n' "$(getprop ro.boot.em.model 2>/dev/null || :)"
printf 'battery=%s\n' "$(cat /sys/class/power_supply/battery/capacity 2>/dev/null || :)"
printf 'data_mount='; awk '$2=="/data" {print $1, $3}' /proc/mounts
printf 'data_free_kib='; df -Pk /data 2>/dev/null | awk 'NR==2 {print $4}'
# Tiny private-file test, never a device path. Preserve a report on stdout.
work=$(mktemp -d /tmp/xnova-tool-probe.XXXXXX) || exit 1
printf 'XNOVA_SELF_TEST\n' > "$work/input"
if timeout 5 dd if="$work/input" of="$work/output" bs=1048576 conv=notrunc,fsync > "$work/dd.log" 2>&1; then
    a=$(sha256sum "$work/input"); b=$(sha256sum "$work/output")
    if [ "${a%% *}" = "${b%% *}" ]; then printf 'dd_fsync=verified\n'; else printf 'dd_fsync=MISMATCH\n'; fi
else
    printf 'dd_fsync=FAILED\n'
    cat "$work/dd.log"
fi
printf 'private_test_path=%s\n' "$work"
printf 'result=capabilities-only-no-flash-no-ZIP64-validation\n'
