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
            result,_=apply(workspace,decoded,patch)
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
