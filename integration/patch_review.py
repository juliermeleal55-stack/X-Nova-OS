# SPDX-License-Identifier: GPL-3.0-or-later
"""Track every prior failed patch; absence of execution is NOT a success."""
import json
from pathlib import Path


def summarize(events, marker):
    baseline=json.loads(Path(__file__).with_name('tolerated_patch_review.json').read_text())
    names=[p['patch'] for p in baseline['patches']]
    if len(names)!=19 or len(set(names))!=19:
        raise ValueError('Incomplete/duplicate prior-failure review baseline')
    results=[]
    for name in names:
        attempts=[e for e in events if e.get('kind')=='patch' and e.get('patch')==name]
        status=('failed' if any(e.get('status')=='failed' for e in attempts) else
                'passed' if attempts and all(e.get('status')=='passed' for e in attempts) else 'not-executed')
        results.append(dict(patch=name,status=status,attempts=len(attempts)))
    return dict(source_run=baseline['source_run'],
                selected_donor=marker.get('donor_profile',{}).get('model','unspecified'),
                scope='Executed patch attempts only; not firmware identity or runtime/boot validation',
                counts={status:sum(e['status']==status for e in results) for status in ('passed','failed','not-executed')},
                patches=results)
