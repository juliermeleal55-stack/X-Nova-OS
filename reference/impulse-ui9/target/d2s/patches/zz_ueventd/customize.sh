# The Android 17 ueventd ignores the legacy /vendor/ueventd.rc, the only place the d2s
# vendor has its device rules (TEEGRIS hangs init without /dev/tzdev and /dev/tziwshmem).
# Named to sort last: earlier target modules still add rules to the vendor file.
LOG "- Adding the d2s device rules to the Android 17 ueventd"
{ echo "# d2s vendor rules"; cat "$WORK_DIR/vendor/ueventd.rc"; } >> "$WORK_DIR/system/system/etc/ueventd.rc"
