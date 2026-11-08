#!/usr/bin/env python3
"""Read-only ADB collection for an installer stall; runs on the user's computer.

Never reboots, mounts, formats, flashes, or kills a process. Output can contain
private device identifiers. Share only with the person diagnosing the failure.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time
import zipfile

FILES = {
    'recovery.log': '/tmp/recovery.log',
    'partition-layout-check.log': '/tmp/partition-layout-check.log',
    'cache-last_log.txt': '/cache/recovery/last_log',
    'cache-last_log.1.txt': '/cache/recovery/last_log.1',
    'cache-log.txt': '/cache/recovery/log',
    'cache-last_kmsg.txt': '/cache/recovery/last_kmsg',
}
COMMANDS = {
    'kernel.txt': 'dmesg',
    'uptime.txt': 'cat /proc/uptime',
    'mounts.txt': 'cat /proc/mounts',
    'diskstats.txt': 'cat /proc/diskstats',
    'meminfo.txt': 'cat /proc/meminfo',
    'processes.txt': 'ps -A || ps',
    'battery.txt': 'cat /sys/class/power_supply/battery/capacity',
}


def capture(adb, args):
    try:
        result = subprocess.run([adb, *args], capture_output=True, timeout=30)
        return result.returncode, result.stdout, result.stderr.decode('utf-8', 'replace')
    except subprocess.TimeoutExpired:
        return 124, b'', 'ADB command timed out after 30 seconds; collection continued.'


def collect(adb, destination, interval=15):
    code, state, error = capture(adb, ['get-state'])
    if code or state.strip() not in (b'recovery', b'device'):
        raise RuntimeError('Connect exactly one device with ADB available in recovery. ' + error)
    destination.mkdir(parents=True, exist_ok=False)
    results = {}

    def save(name, command):
        code, output, error = capture(adb, ['shell', command])
        (destination / name).write_bytes(output)
        results[name] = {'exit_code': code, 'stderr': error}
        print(name + (' OK' if code == 0 else ' unavailable/error (recorded)'))

    # Collect retained logs FIRST: a new recovery boot replaces /tmp/recovery.log.
    for name, remote in FILES.items():
        save(name, 'cat ' + remote)
    for sample in (1, 2):
        for name, command in COMMANDS.items():
            save(str(sample) + '-' + name, command)
        if sample == 1:
            time.sleep(interval)
    # Capture changes during the observation interval, without restarting install.
    save('recovery-final.log', 'cat /tmp/recovery.log')
    (destination / 'collection.json').write_text(json.dumps({
        'utc': datetime.now(timezone.utc).isoformat(),
        'interval_seconds': interval,
        'warning': 'May contain private identifiers. Not a diagnosis or a repair.',
        'results': results,
    }, indent=2), encoding='utf-8')
    archive = destination / 'recovery-stall.zip'
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as handle:
        for file in sorted(destination.iterdir()):
            if file != archive:
                handle.write(file, file.name)
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb', default='adb', help='Path to adb (for example ./adb.exe)')
    parser.add_argument('--output', type=Path, default=Path('recovery-stall-' + datetime.now().strftime('%Y%m%d-%H%M%S')))
    args = parser.parse_args()
    try:
        archive = collect(args.adb, args.output)
    except (OSError, RuntimeError) as error:
        parser.exit(1, str(error) + '\n')
    print('Send this archive privately: ' + str(archive.resolve()))


if __name__ == '__main__':
    main()
