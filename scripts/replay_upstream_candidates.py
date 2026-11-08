#!/usr/bin/env python3
"""Strict replay on exact retained inputs. Does NOT assemble/boot or download ROM."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.smali_patch import apply
from integration.smali_paths import resolve

ROOT=Path(__file__).resolve().parents[1]


def fixed_boolean(text, field):
    """Prove an unchanged constant from the entry block; otherwise unknown.

    Reject any other write to the register before the field store. No CFG/value
    inference across branches or arbitrary donor register-number assumptions.
    """
    methods=re.findall(r'(?ms)^\.method [^\n]*<clinit>\(\)V\n(.*?)^\.end method',text)
    if len(methods)!=1:return 'unknown'
    body=methods[0]
    stores=list(re.finditer(r'(?m)^\s*sput-boolean ([vp][0-9]+), L[^;]+;->'+re.escape(field)+r':Z\s*$',body))
    if len(stores)!=1:return 'unknown'
    register=stores[0][1];lines=body[:stores[0].start()].splitlines()
    branch=next((i for i,line in enumerate(lines) if re.match(r'^(?::|if-|goto|packed-switch|sparse-switch|return|throw)',line.strip())),len(lines))
    writers=[]
    for i,line in enumerate(lines):
        line=line.strip()
        if not line or line.startswith(('.',':','#')):continue
        if re.match(r'^(?:invoke-|filled-new-array|if-|goto|[ais]put|monitor-|return|throw|packed-switch|sparse-switch|fill-array-data|nop)',line):continue
        if re.match(r'^\S+ '+register+r'(?:,|$)',line):writers.append((i,line))
    if not writers or writers[0][0]>=branch:return 'unknown'
    constants=[re.fullmatch(r'const/(?:4|16) '+register+r', (0x[01])',line) for _,line in writers]
    if not all(constants) or len({m[1] for m in constants})!=1:return 'unknown'
    return constants[0][1]=='0x1'


def fingerprint_facts(decoded, spec):
    if spec['id'] not in ('fingerprint-service','fingerprint-systemui'):return None
    if spec['id']=='fingerprint-service':
        target='smali/com/android/server/biometrics/SemBiometricFeature.smali'
        fields=['FP_FEATURE_SENSOR_IS_IN_DISPLAY_TYPE','FP_FEATURE_SENSOR_IS_OPTICAL']
    else:
        target='smali/com/android/systemui/LsRune.smali'
        fields=['SECURITY_FINGERPRINT_IN_DISPLAY','SECURITY_FINGERPRINT_IN_DISPLAY_OPTICAL']
    text=resolve(decoded,target).read_text()
    return {field:fixed_boolean(text,field) for field in fields}


def replay(artifacts):
    reports=list(artifacts.rglob('patch-preflight.json'))
    if len(reports)!=1:raise ValueError('Expected exactly one donor patch report')
    report=json.loads(reports[0].read_text())
    sources={hashlib.sha256(p.read_bytes()).hexdigest():p for p in artifacts.rglob('*.smali') if p.is_file() and not p.is_symlink()}
    results=[]
    specs=json.loads((ROOT/'integration/boot_patch_candidates.json').read_text())
    for spec in specs:
        item=dict(spec,status='unavailable')
        results.append(item)
        matches=[e for e in report['events'] if e.get('patch')==spec['original_patch'] and e.get('kind')=='patch']
        if len(matches)!=1 or not matches[0].get('inputs'):
            item['reason']='Exact original class inputs not retained';continue
        inputs=matches[0]['inputs']
        if any(digest not in sources for digest in inputs.values()):
            item['reason']='A required original input hash is absent';continue
        with tempfile.TemporaryDirectory() as tmp:
            workspace=Path(tmp);prefixes=set()
            for name,digest in inputs.items():
                parts=Path(name).parts
                if Path(name).is_absolute() or '..' in parts:raise ValueError('Unsafe original class input path')
                indexes=[i for i,p in enumerate(parts) if re.fullmatch(r'smali(?:_classes[1-9][0-9]*)?',p)]
                if len(indexes)!=1:raise ValueError('Expected one DEX directory in captured input')
                prefixes.add(Path(*parts[:indexes[0]]))
                dest=workspace/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(sources[digest],dest)
            if len(prefixes)!=1:raise ValueError('Inputs span multiple decoded artifacts')
            decoded=workspace/next(iter(prefixes))
            candidate=ROOT/spec['candidate']
            if not candidate.resolve().is_relative_to((ROOT/'reference/boot-patch-audit').resolve()):raise ValueError('Unsafe candidate source')
            raw=candidate.read_text()
            # Do not infer missing input for extra classes touched by the candidate.
            try:
                for target in re.findall(r'(?m)^\+\+\+ b/(.+)$',raw):resolve(decoded,target)
            except ValueError:
                item['reason']='Candidate needs additional/absent class input';continue
            patch=workspace/'candidate.patch';patch.write_text(raw)
            before=fingerprint_facts(decoded,spec)
            result,_=apply(workspace,decoded,patch)
            if before is not None and result.returncode==0:
                item['constant_evidence']={'before':before,'after':fingerprint_facts(decoded,spec)}
            item['status']='applied-to-retained-input' if result.returncode==0 else 'rejected'
            item['reason']='Strict git apply; original input hashes matched' if result.returncode==0 else 'Candidate context rejected by strict apply'
    return dict(scope='Exact retained diagnostic inputs only; NOT assembly/runtime/boot validation',source_run=42419957346,results=results)


if __name__=='__main__':
    result=replay(Path(sys.argv[1]));print(json.dumps(result,indent=2))
    Path('upstream-candidate-replay.json').write_text(json.dumps(result,indent=2)+'\n')
    text=json.dumps(result)
    for i in range(0,len(text),2800):
        chunk=text[i:i+2800].replace('%','%25').replace('\r','%0D').replace('\n','%0A')
        print(f'::notice title=Upstream-candidate-replay-{i//2800}::{chunk}')
