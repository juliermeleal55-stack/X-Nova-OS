#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Lossless logical DEX planning and descriptor inventory, including DEX 041.

Inspired by ImpulseROM's logical-unit enumeration (see IMPULSE-UI9-ANALYSIS).
Does not decode/assemble itself, infer classes, or restore cached containers.
"""
import json
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import zipfile

PHYSICAL=re.compile(r'classes(?:[2-9]|[1-9][0-9]+)?\.dex')
DESCRIPTOR=re.compile(r'L[^\s;]+;')
MAP='dex_logical_map.json'


def command(*args):
    return subprocess.run(['baksmali',*args],check=True,capture_output=True,text=True).stdout


def units(physical, listed):
    if len(physical)!=len(set(physical)) or not physical or 'classes.dex' not in physical:raise ValueError('Missing/duplicate primary physical DEX')
    if any(not PHYSICAL.fullmatch(p) for p in physical):raise ValueError('Unsupported physical DEX name')
    entries=listed.splitlines()
    if not entries or len(entries)!=len(set(entries)):raise ValueError('Empty/duplicate logical DEX listing')
    by_file={p:[] for p in physical}
    for entry in entries:
        parts=entry.split('/')
        if len(parts)>2 or parts[0] not in by_file:raise ValueError('Unexpected logical DEX selector')
        if len(parts)==2 and (not re.fullmatch('[1-9][0-9]*',parts[1]) or int(parts[1])<2):raise ValueError('Unsafe logical DEX ordinal')
        by_file[parts[0]].append(entry)
    ordered=[]
    for physical_name in sorted(physical,key=lambda p:1 if p=='classes.dex' else int(p[7:-4])):
        group=sorted(by_file[physical_name],key=lambda p:1 if '/' not in p else int(p.split('/')[1]))
        expected=[physical_name]+[physical_name+'/'+str(i) for i in range(2,len(group)+1)]
        if group!=expected:raise ValueError('Missing/noncontiguous logical DEX units')
        ordered.extend(group)
    return [dict(entry=e,smali='smali' if i==1 else f'smali_classes{i}',output='classes.dex' if i==1 else f'classes{i}.dex') for i,e in enumerate(ordered,1)]


def create(source):
    with zipfile.ZipFile(source) as archive:
        physical=[n for n in archive.namelist() if PHYSICAL.fullmatch(n)]
    return dict(schema_version=1,units=units(physical,command('list','dex',str(source))))


def load(decoded):
    data=json.loads((decoded/MAP).read_text())
    if data.get('schema_version')!=1 or not data.get('units'):raise ValueError('Invalid logical DEX map')
    physical=list(dict.fromkeys(u['entry'].split('/')[0] for u in data['units']))
    if data['units']!=units(physical,'\n'.join(u['entry'] for u in data['units'])):raise ValueError('Altered logical DEX mapping')
    return data


def descriptors(directory):
    if not directory.is_dir() or directory.is_symlink():raise ValueError('Missing/unsafe decoded DEX directory')
    result=set()
    for p in directory.rglob('*.smali'):
        if p.is_symlink() or not p.resolve().is_relative_to(directory.resolve()):raise ValueError('Unsafe decoded class')
        names=re.findall(r'(?m)^\.class[^\n]* (L[^\s]+;)\s*$',p.read_text())
        expected='L'+p.relative_to(directory).as_posix()[:-6]+';'
        if names!=[expected] or expected in result:raise ValueError('Invalid/duplicate decoded descriptor')
        result.add(expected)
    return result


def verify_decode(source, decoded, evidence=None):
    data=load(decoded);seen=set();inventory={}
    actual_dirs={p.name for p in decoded.iterdir() if p.name.startswith('smali') and p.is_dir()}
    if actual_dirs!={u['smali'] for u in data['units']}:raise ValueError('Unexpected decoded DEX directories')
    for unit in data['units']:
        raw=command('list','classes',str(source)+'/'+unit['entry']).splitlines()
        if any(not DESCRIPTOR.fullmatch(n) for n in raw) or len(set(raw))!=len(raw):raise ValueError('Invalid source class listing')
        expected=set(raw);actual=descriptors(decoded/unit['smali'])
        if actual!=expected:raise ValueError(f"Decoded DEX class inventory mismatch: {unit['smali']}; expected={len(expected)} decoded={len(actual)}")
        if seen & expected:raise ValueError('Duplicate class across logical DEX units')
        seen.update(expected);inventory[unit['smali']]=sorted(expected)
    (decoded/'dex_class_inventory.json').write_text(json.dumps(inventory)+'\n')
    if evidence is not None:
        digest=hashlib.sha256()
        with source.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
        with zipfile.ZipFile(source) as archive:
            summary=[]
            for unit in data['units']:
                with archive.open(unit['entry'].split('/')[0]) as stream:magic=stream.read(8).hex()
                summary.append(dict(unit,classes=len(inventory[unit['smali']]),physical_magic=magic))
        evidence.mkdir(parents=True,exist_ok=True)
        (evidence/(source.name+'-'+digest.hexdigest()[:12]+'.json')).write_text(json.dumps(dict(source_sha256=digest.hexdigest(),status='decode-inventory-verified',units=summary,unique_classes=len(seen)),indent=2)+'\n')
    print(f'Logical DEX inventory verified: {len(inventory)} units, {len(seen)} unique classes')


def build_rows(decoded):
    data=load(decoded);rows={}
    for row in (decoded/'dex_api_versions.tsv').read_text().splitlines():
        fields=row.split('\t')
        if len(fields)!=2 or fields[0] in rows or not fields[1].isdigit() or not 1<=int(fields[1])<=35:raise ValueError('Invalid/duplicate DEX API metadata')
        rows[fields[0]]=int(fields[1])
    mapped={u['smali'] for u in data['units']}
    if not mapped<=rows.keys():raise ValueError('Missing original DEX API metadata')
    extras=set(rows)-mapped
    dirs={p.name for p in decoded.iterdir() if p.name.startswith('smali') and p.is_dir()}
    if extras-dirs:raise ValueError('Stale DEX API metadata')
    count=len(dirs);ordered=['smali']+[f'smali_classes{i}' for i in range(2,count+1)]
    if dirs!=set(ordered) or not mapped<=dirs:raise ValueError('Missing/noncontiguous original or added DEX directory')
    inventory=json.loads((decoded/'dex_class_inventory.json').read_text())
    if set(inventory)!=mapped:raise ValueError('Incomplete original class inventory')
    seen=set()
    for name in ordered:
        actual=descriptors(decoded/name)
        if seen & actual:raise ValueError('Duplicate class before DEX assembly')
        if not set(inventory.get(name,[]))<=actual:raise ValueError('Original class lost before DEX assembly')
        seen.update(actual)
    default=max(rows[name] for name in mapped)
    return [(name,rows[name] if name in mapped else default,'classes.dex' if i==1 else f'classes{i}.dex') for i,name in enumerate(ordered,1)]


def main():
    action=sys.argv[1]
    if action=='plan':
        source=Path(sys.argv[2]);decoded=Path(sys.argv[3]);data=create(source)
        (decoded/MAP).write_text(json.dumps(data,indent=2)+'\n')
        for u in data['units']:print(u['entry']+'\t'+u['smali'])
    elif action=='verify-decode':verify_decode(Path(sys.argv[2]),Path(sys.argv[3]),Path(sys.argv[4]) if len(sys.argv)>4 else None)
    elif action=='build-rows':
        for row in build_rows(Path(sys.argv[2])):print('\t'.join(map(str,row)))
    else:raise ValueError('Unknown logical DEX operation')


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,subprocess.CalledProcessError,zipfile.BadZipFile) as exc:
        detail=(exc.stderr or '')[-2000:] if isinstance(exc,subprocess.CalledProcessError) else ''
        print('Logical DEX integrity blocked: '+str(exc)+'\n'+detail,file=sys.stderr);sys.exit(1)
