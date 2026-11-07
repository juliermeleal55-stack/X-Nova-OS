#!/usr/bin/env python3
"""Always distinguish prerequisite failures from executed patch diagnostics."""
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.patch_review import summarize


def collect(workspace):
    def read(path):
        return json.loads(path.read_text()) if path.is_file() else None
    marker=read(workspace/'BEYOUD-WORKSPACE.json') or {}
    logs=workspace/'out/beyoud-logs';logs.mkdir(parents=True,exist_ok=True)
    report=read(logs/'patch-preflight.json')
    events=report.get('events',[]) if report else []
    partial=logs/'patch-preflight.jsonl'
    if not report and partial.is_file():
        for line in partial.read_text().splitlines():
            try:events.append(json.loads(line))
            except json.JSONDecodeError:break
    summary=dict(schema_version=1,scope='Diagnosis only; no ROM created or boot tested',
                 status=report['status'] if report else ('incomplete' if events else 'not-executed'),
                 selected_donor=marker.get('donor_profile'),
                 firmware_lock=read(workspace/'out/firmware-lock.json'),
                 actual_firmware_inspection=read(workspace/'out/beyoud-firmware-inspection.json'),
                 stage_receipts={p.stem:read(p) for p in sorted((workspace/'out/beyoud-stages').glob('*.json'))},
                 prior_19_review=summarize(events,marker),
                 failures=[e for e in events if e.get('status')=='failed'])
    (logs/'patch-diagnostic-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    text='# S24 FE patch diagnostic\n\nStatus: **'+summary['status']+'**. No ROM generated.\n\n'
    text+='Previous 19 patches: `'+json.dumps(summary['prior_19_review']['counts'])+'`\n\n'
    text+='See patch-diagnostic-summary.json, patch-preflight.json and per-module logs in the diagnostics artifact. '
    text+='A prerequisite failure means the patches were not tested; it is not a clean patch pass.\n'
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as stream:stream.write(text)
    print(text)
    print('::notice title=Patch diagnostic result::'+summary['status']+'; previous 19: '+json.dumps(summary['prior_19_review']['counts']))
    return summary


if __name__=='__main__':collect(Path(sys.argv[1]).resolve())
