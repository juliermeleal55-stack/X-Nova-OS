#!/usr/bin/env python3
"""Validate the independent probe on hash-checked, unmodified S24 FE donor inputs.

Needs the pinned workspace baksmali on PATH. Never patches, assembles or signs.
Only JSON evidence is retained; donor binaries/decoded files are not published.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integration.dex_container_probe import inspect, verify_mapping
from integration.dex_entries import create, verify_decode


def validate(inputs, output):
    manifest = json.loads((inputs / 'repair-inputs.json').read_text())
    if manifest['model'] != 'SM-S721B' or not manifest['version'].startswith('S721BXXSFEZJ1/'):
        raise ValueError('Expected the configured S24 FE S721BXXSFEZJ1 donor, not historical S926B inputs')
    output.mkdir(parents=True, exist_ok=False)
    report = {'model': manifest['model'], 'version': manifest['version'], 'files': [], 'status': 'in-progress'}
    failures = []
    for item in manifest['files']:
        if item.get('status') != 'captured' or Path(item['name']).suffix not in {'.apk', '.jar'}:
            continue
        name = item['name']
        if Path(name).name != name:
            raise ValueError('Unsafe manifest filename')
        source = inputs / name
        result = {'name': name, 'source_sha256': item['sha256']}
        try:
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if digest != item['sha256'] or source.stat().st_size != item['size']:
                raise ValueError('Retained input hash/size differs from original capture')
            entries = inspect(source)
            mapping = create(source)
            with tempfile.TemporaryDirectory(prefix='s24fe-dex-') as temporary:
                decoded = Path(temporary)
                (decoded / 'dex_logical_map.json').write_text(json.dumps(mapping))
                for unit in mapping['units']:
                    subprocess.run(['baksmali', 'd', '--ac', 'false', '--di', 'false', '-j', '1', '-l',
                                    '-o', str(decoded / unit['smali']), '--sl', str(source) + '/' + unit['entry']],
                                   check=True, timeout=600)
                result.update(verify_mapping(entries, decoded, mapping))
                # Separate exact descriptor identity check, not just equal counts.
                verify_decode(source, decoded, output)
                result['descriptor_identity_verified'] = True
        except (ValueError, OSError, subprocess.SubprocessError) as error:
            result.update(status='failed', error=str(error))
            failures.append(name)
        report['files'].append(result)
        (output / 's24fe-independent-probe.json').write_text(json.dumps(report, indent=2) + '\n')
    names = {item['name'] for item in report['files']}
    if not {'framework.jar', 'services.jar', 'SystemUI.apk', 'SecSettings.apk'} <= names:
        failures.append('required-framework-or-UI-input-missing')
    report['status'] = 'failed' if failures else 'verified'
    report['failures'] = failures
    (output / 's24fe-independent-probe.json').write_text(json.dumps(report, indent=2) + '\n')
    summary = {'status': report['status'], 'model': report['model'],
               'files': [{key: item.get(key) for key in ('name', 'status', 'logical_units', 'total_class_defs', 'error')}
                         for item in report['files']]}
    print('::notice title=S24 FE independent DEX probe::' + json.dumps(summary))
    if failures:
        raise ValueError('Real-input validation failed: ' + ', '.join(failures))


if __name__ == '__main__':
    if shutil.which('baksmali') is None:
        sys.exit('Pinned workspace baksmali must be on PATH')
    validate(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
