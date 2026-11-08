# exynos9825 ships a newer HWC build that advertises a single display mode. The stock
# one reads every panel resolution from psr_info, which the resolution setting needs.
LOG_STEP_IN "- Restoring the stock d2s graphics HAL"
while read -r blob; do
    [ -n "$blob" ] || continue
    ADD_TO_WORK_DIR "$TARGET_FIRMWARE" "vendor" "$blob"
done <<'EOF'
bin/hw/android.hardware.graphics.composer@2.2-service
bin/hw/android.hardware.graphics.allocator@2.0-service
bin/hw/vendor.samsung_slsi.hardware.ExynosHWCServiceTW@1.0-service
lib64/libexynosdisplay.so
lib64/libExynosHWCService.so
lib64/libacryl.so
lib64/libion_exynos.so
lib64/vendor.samsung_slsi.hardware.ExynosHWCServiceTW@1.0.so
lib64/android.hardware.graphics.composer@2.1.so
lib64/android.hardware.graphics.composer@2.1-resources.so
lib64/android.hardware.graphics.composer@2.2.so
lib64/android.hardware.graphics.composer@2.2-resources.so
lib64/hw/hwcomposer.exynos9825.so
lib64/hw/gralloc.exynos9825.so
lib64/hw/gralloc.default.so
lib64/hw/android.hardware.graphics.allocator@2.0-impl.so
lib/libexynosdisplay.so
lib/libExynosHWCService.so
lib/libacryl.so
lib/libion_exynos.so
lib/hw/hwcomposer.exynos9825.so
lib/hw/gralloc.exynos9825.so
lib/hw/gralloc.default.so
lib/hw/android.hardware.graphics.allocator@2.0-impl.so
EOF
LOG_STEP_OUT
