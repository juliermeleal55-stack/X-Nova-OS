#!/usr/bin/env bash
# First One UI 9 build attempt (source S721B FEZJ1) in ~/ImpulseROM-9. Dev-signed test build.
export PATH="$HOME/.local/bin:$PATH"
cd "$HOME/ImpulseROM-9" || exit 1
export GIT_COMMITTER_NAME="ImpulseROM Builder" GIT_COMMITTER_EMAIL="builder@localhost"
export GIT_AUTHOR_NAME="$GIT_COMMITTER_NAME" GIT_AUTHOR_EMAIL="$GIT_COMMITTER_EMAIL"
export APKTOOL_PARALLEL_JOBS=1 APKTOOL_THREAD_COUNT=2 TERM=dumb
export PATCH_DRIFT_POLICY=skip
export FIRMWARE_PIN_SM_S721B_EUX="S721BXXSFEZJ1/S721BOXMFEZJ1/S721BXXSFEZJ1/S721BXXSFEZJ1"
export IMPULSE_DONOR_BUILD="S721BXXSFEZJ1/S721BOXMFEZJ1/S721BXXSFEZJ1"
export IMPULSE_DONOR_API=37 IMPULSE_DONOR_RELEASE=17
export FIRMWARE_PIN_SM_S711B_EUX="S711BXXSGGZF2/S711BOXMGGZF2/S711BXXSGGZF2/S711BXXSGGZF2"
export FIRMWARE_PIN_SM_N975F_BTU="N975FXXS9HWHA/N975FOXM9HWH6/N975FXXS9HWH6/N975FXXS9HWHA"
echo "building $(git rev-parse --short HEAD) on $(git branch --show-current)"; date -Is
source buildenv.sh d2s || { echo "ABORT: buildenv.sh failed"; exit 1; }
./scripts/make_rom.sh --force
RC=$?
echo "make_rom.sh exit code: $RC"; date -Is
ls -l out/*.zip 2>/dev/null
exit $RC
