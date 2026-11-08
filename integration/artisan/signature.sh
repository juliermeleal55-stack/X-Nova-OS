# X-Nova scoped platform bridge, derived from ImpulseROM; no global bypass.
DECODE_APK "system" "system/framework/services.jar" || exit 1
APPLY_PATCH "system" "system/framework/services.jar" "$MODPATH/0001-Allow-custom-platform-signature.patch"
CERT_PREFIX="aosp"
$ROM_IS_OFFICIAL && CERT_PREFIX="extremerom"
# The experimental collector may continue after APPLY_PATCH fails. Configuration
# validates the full bridge and its unique marker; a no-op sed cannot pass here.
python3 "$SRC_DIR/integration/signature_bridge.py" configure \
    "$APKTOOL_DIR/system/framework/services.jar" \
    "$SRC_DIR/security/${CERT_PREFIX}_platform.x509.pem" \
    "$SRC_DIR/out/beyoud-logs/platform-signature.json" || exit 1
unset CERT_PREFIX
