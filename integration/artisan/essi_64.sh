# SPDX-License-Identifier: GPL-3.0-or-later
# S24 FE donor -> historical Artisan build API. No S10 hardware config is imported.
# Upstream revision and original notices: integration/donors/s24fe.json and .sh.
# SDK/layout are declarations until checked against the downloaded firmware.
source "$SRC_DIR/integration/donors/s24fe.sh" || return 1
# Aliases retained for helpers that consume the newer UN1CA variable names.
SOURCE_PLATFORM_SDK_VERSION="$SOURCE_API_LEVEL"
SOURCE_PRODUCT_SHIPPING_API_LEVEL="$SOURCE_PRODUCT_FIRST_API_LEVEL"
SOURCE_BOARD_API_LEVEL="$SOURCE_VNDK_VERSION"
