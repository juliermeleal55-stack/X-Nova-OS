#!/usr/bin/env bash
set -euo pipefail

module="${1:?module path required}"
framework="${2:?decoded framework directory required}"
temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT
d8="${D8:-$(command -v d8 || true)}"
if [[ ! -x "$d8" ]]; then
    d8="$(dirname "$(readlink -f "$(command -v apksigner)")")/d8"
fi
if [[ ! -x "$d8" ]]; then
    printf 'Android build-tools d8 is required for signed-app code overrides\n' >&2
    exit 1
fi
mkdir -p "$temporary/classes" "$temporary/dex"
javac --release 8 -d "$temporary/classes" "$module/src/com/android/internal/os/S10AppCodeOverrides.java"
"$d8" --min-api 28 --no-desugaring --output "$temporary/dex" \
    "$temporary/classes/com/android/internal/os/S10AppCodeOverrides.class"
baksmali disassemble "$temporary/dex/classes.dex" --output "$temporary/smali"
mkdir -p "$framework/smali/com/android/internal/os"
cp "$temporary/smali/com/android/internal/os/S10AppCodeOverrides.smali" "$framework/smali/com/android/internal/os/"