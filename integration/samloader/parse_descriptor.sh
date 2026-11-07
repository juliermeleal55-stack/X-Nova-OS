# SPDX-License-Identifier: GPL-3.0-or-later
# SmartDownload uses model/CSC and a separate, resolved firmware lock.
# An optional legacy third token is never sent as a device identifier.
PARSE_FIRMWARE_STRING()
{
    local descriptor="$1"
    # Clear legacy state on EVERY call, including failed parses.
    MODEL=""
    CSC=""
    IMEI=""
    SERIAL_NO=""
    if [[ ! "$descriptor" =~ ^(SM-[A-Z0-9]+)/([A-Z0-9]{3})(/[A-Za-z0-9]+)?$ ]]; then
        LOGE "Invalid firmware descriptor: expected MODEL/CSC with optional legacy/reference token"
        return 1
    fi
    MODEL="${BASH_REMATCH[1]}"
    CSC="${BASH_REMATCH[2]}"
    return 0
}
