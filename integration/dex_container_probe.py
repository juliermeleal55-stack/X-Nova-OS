#!/usr/bin/env python3
"""Sonda somente-leitura de containers DEX (sem baksmali).

Lista as unidades DEX lógicas de cada classes*.dex e soma class_defs_size, para
conferir de forma INDEPENDENTE o que o decodificador (baksmali) produziu.

Layout assumido (AOSP dex-format; CONFIRMAR no primeiro arquivo real): cabeçalho de
0x70 bytes; a versão 041 acrescenta container_size @0x70 e header_offset @0x74
(header_size 0x78). Qualquer inconsistência levanta ValueError; nada é adivinhado.

Uso:  dex_container_probe.py <jar|apk|dex> [--smali-dir <pasta apktool>]
Saída: JSON. Código 0 = ok, 1 = formato inválido, 2 = classes decodificadas != class_defs.
"""
import argparse
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

MAGIC = re.compile(rb'dex\n(\d{3})\x00')
PHYSICAL = re.compile(r'(?:.*/)?classes(?:[2-9]|[1-9][0-9]+)?\.dex')


def _header(data, pos, name):
    head = bytes(data[pos:pos + 0x78])
    match = MAGIC.fullmatch(head[:8]) if len(head) >= 8 else None
    if not match or len(head) < 0x70:
        raise ValueError(f'{name}: cabecalho DEX invalido no offset {pos}')
    version = int(match.group(1))
    if version not in {35, 37, 38, 39, 40, 41}:
        raise ValueError(f'{name}: versao DEX nao suportada: {version}')
    if struct.unpack_from('<I', head, 0x28)[0] != 0x12345678:
        raise ValueError(f'{name}: endian_tag invalido/nao suportado')
    file_size, header_size = struct.unpack_from('<II', head, 0x20)
    unit = {'offset': pos, 'version': version, 'file_size': file_size,
            'header_size': header_size,
            'class_defs': struct.unpack_from('<I', head, 0x60)[0]}
    if version >= 41:
        if len(head) < 0x78:
            raise ValueError(f'{name}: cabecalho 041 truncado no offset {pos}')
        unit['container_size'], unit['header_offset'] = struct.unpack_from('<II', head, 0x70)
    return unit


def units(data, name='<dex>'):
    first = _header(data, 0, name)
    if first['version'] < 41:
        if first['header_size'] != 0x70 or first['file_size'] < 0x70:
            raise ValueError(f'{name}: tamanho de cabecalho/arquivo invalido')
        if first['file_size'] != len(data):
            raise ValueError(f'{name}: file_size diferente do tamanho real')
        first['trailing_bytes'] = len(data) - first['file_size']
        return [first]
    result, pos = [], 0
    while pos < len(data):
        unit = _header(data, pos, name)
        if unit['version'] < 41:
            raise ValueError(f'{name}: unidade nao-041 dentro de container em {pos}')
        if unit['header_size'] != 0x78:
            raise ValueError(f'{name}: header_size {unit["header_size"]:#x} != 0x78 em {pos}')
        if unit['header_offset'] != pos:
            raise ValueError(f'{name}: header_offset {unit["header_offset"]} != {pos}')
        if unit['container_size'] != len(data):
            raise ValueError(f'{name}: container_size {unit["container_size"]} != {len(data)}')
        if unit['file_size'] < 0x78 or pos + unit['file_size'] > len(data):
            raise ValueError(f'{name}: file_size invalido em {pos}')
        result.append(unit)
        pos += unit['file_size']
        pad = -pos % 4
        if pos < len(data) and pad and data[pos:pos + pad] == b'\0' * pad:
            pos += pad
    return result


def inspect(path):
    path = Path(path)
    entries = []
    if path.suffix.lower() in {'.apk', '.jar', '.zip'} or zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            physical = [n for n in archive.namelist() if '/' not in n and PHYSICAL.fullmatch(n)]
            if not physical or 'classes.dex' not in physical or len(set(physical)) != len(physical):
                raise ValueError('DEX primario ausente ou entradas DEX duplicadas')
            names = sorted(physical,
                           key=lambda n: 1 if n.endswith('classes.dex') else int(re.search(r'classes(\d+)', n).group(1)))
            blobs = [(n, archive.read(n)) for n in names]
    else:
        blobs = [(path.name, path.read_bytes())]
    for name, data in blobs:
        found = units(data, name)
        entries.append({'entry': name, 'size': len(data), 'version': found[0]['version'],
                        'logical_units': len(found), 'units': found,
                        'class_defs': sum(u['class_defs'] for u in found)})
    return entries


def count_smali(root):
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError('Pasta Smali ausente/insegura')
    total = 0
    for directory in root.iterdir():
        if re.fullmatch(r'smali(?:_classes[0-9]+)?', directory.name):
            total += count_directory(directory)
    return total


def count_directory(directory):
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError('Unidade Smali ausente/insegura')
    files = list(directory.rglob('*.smali'))
    if any(p.is_symlink() or not p.resolve().is_relative_to(directory.resolve()) for p in files):
        raise ValueError('Arquivo Smali inseguro')
    return len(files)


def verify_mapping(entries, decoded, mapping):
    """Independent header counts versus every baksmali selector and decoded unit.

    This complements descriptor identity verification; it never replaces it.
    """
    selectors = [entry['entry'] + ('' if i == 0 else '/' + str(i + 1))
                 for entry in entries for i, _ in enumerate(entry['units'])]
    expected = [{'entry': selector,
                 'smali': 'smali' if i == 1 else f'smali_classes{i}',
                 'output': 'classes.dex' if i == 1 else f'classes{i}.dex'}
                for i, selector in enumerate(selectors, 1)]
    if mapping.get('schema_version') != 1 or mapping.get('units') != expected:
        raise ValueError('Mapa baksmali difere das unidades DEX independentes')
    directories = {p.name for p in decoded.iterdir() if p.name.startswith('smali')}
    if directories != {row['smali'] for row in expected}:
        raise ValueError('Diretorios Smali inesperados/ausentes')
    counts = [unit['class_defs'] for entry in entries for unit in entry['units']]
    for row, count in zip(expected, counts):
        actual = count_directory(decoded / row['smali'])
        if actual != count:
            raise ValueError(f"Contagem independente difere em {row['smali']}: header={count}, smali={actual}")
    return {'status': 'independent-header-counts-verified', 'entries': entries,
            'total_class_defs': sum(counts), 'logical_units': len(counts)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('path')
    parser.add_argument('--smali-dir')
    args = parser.parse_args(argv)
    try:
        entries = inspect(args.path)
        decoded_count = count_smali(args.smali_dir) if args.smali_dir else None
    except (ValueError, OSError, zipfile.BadZipFile) as error:
        print(f'ERRO: {error}', file=sys.stderr)
        return 1
    report = {'path': args.path, 'entries': entries,
              'total_class_defs': sum(e['class_defs'] for e in entries)}
    code = 0
    if args.smali_dir:
        report['decoded_smali_files'] = decoded_count
        if report['decoded_smali_files'] != report['total_class_defs']:
            report['mismatch'] = True
            code = 2
    print(json.dumps(report, indent=2))
    return code


if __name__ == '__main__':
    sys.exit(main())
