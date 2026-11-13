#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Inspect actual firmware identity/SDK/layout and retain evidence on failure."""
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integration.package_inputs import atomic_json, read_prop
from integration.samloader.metadata import configured_firmwares, get
from integration.targets import from_marker


def system_ext_layout(root):
    separate_path=root/'system_ext'
    embedded_path=root/'system/system/system_ext'
    for path in (separate_path,embedded_path):
        if path.is_symlink() and not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Unsafe system_ext alias outside extracted firmware')
    separate=separate_path.is_dir()
    embedded=embedded_path.is_dir()
    alias=separate and embedded and separate_path.samefile(embedded_path)
    if alias:separate=False
    if separate and embedded:
        raise ValueError('Ambiguous independent separate and embedded system_ext trees')
    return dict(separate_system_ext=separate,embedded_system_ext=embedded,
                system_ext_alias=alias,system_ext_layout='separate' if separate else 'embedded' if embedded else 'absent')


def inspect(workspace):
    marker=json.loads((workspace/'BEYOUD-WORKSPACE.json').read_text())
    codename,device=from_marker(marker)
    donor=marker.get('donor_profile')
    out=workspace/'out'
    config=dict(re.findall(r'^([A-Z_]+)="([^"\n]*)"$',(out/'config.sh').read_text(),re.M))
    result=dict(schema_version=1,codename=codename,status='inspecting',firmwares=[])
    destination=out/'beyoud-firmware-inspection.json'
    try:
        for role,descriptor in zip(('source','target'),configured_firmwares(out/'config.sh')):
            model,csc,*_=descriptor.split('/')
            record=get(out/'firmware-lock.json',model,csc)
            if role=='source' and donor and (model,csc)!=(donor['model'],donor['csc']):
                raise ValueError('Source firmware does not match selected donor model/CSC')
            if role=='target' and model!=device['model']:
                raise ValueError('Wrong stock target firmware')
            root=out/'fw'/f'{model}_{csc}'
            if root.is_symlink() or not root.resolve().is_relative_to(workspace.resolve()):
                raise ValueError('Unsafe extracted firmware root')
            if (root/'.extracted').read_text().strip()!=record['version']:
                raise ValueError('Firmware extraction differs from lock')
            prop=root/'system/system/build.prop'
            if not prop.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe firmware property path')
            sdk=read_prop(prop,'ro.build.version.sdk')
            observation=dict(role=role,model=model,csc=csc,version=record['version'],sdk=int(sdk))
            result['firmwares'].append(observation)
            # Optional values are evidence, not claims inferred from the source comments.
            for key in ('ro.build.version.release','ro.build.version.oneui','ro.build.version.incremental'):
                values=re.findall(r'^'+re.escape(key)+r'=(.*)$',prop.read_text(),re.M)
                observation[key]=values[0].strip() if len(values)==1 else None
            observation.update(system_ext_layout(root))
            expected=config[f'{role.upper()}_API_LEVEL']
            if sdk!=expected:
                raise ValueError(f'{role} actual SDK={sdk}, declared SDK={expected}; select/adapt the donor schema, do not bypass this check')
            if role=='source' and donor:
                if int(sdk)!=donor['declared_sdk']:
                    raise ValueError('Actual source SDK differs from selected S24 FE donor profile; adapt after inspection')
                if record['version'].split('/')[0]!=donor['reference_ap']:
                    raise ValueError('Actual source AP differs from selected S24 FE donor profile; do not change the pinned donor')
                if record['version']!=donor.get('reference_version'):
                    raise ValueError('Actual source full version differs from the exact S24 FE reference version')
            present=observation['separate_system_ext'] or observation['embedded_system_ext']
            if role=='source' and config.get('SOURCE_HAS_SYSTEM_EXT')=='true' and not present:
                raise ValueError('Declared donor system_ext is absent; adapter layout needs review')
            # false means no SEPARATE partition, not no embedded directory.
            if role=='source' and donor and config.get('SOURCE_HAS_SYSTEM_EXT')=='false' and observation['separate_system_ext']:
                raise ValueError('Unexpected source system_ext separate partition; inspect before adapting layout')
        if len(result['firmwares'])!=2:raise ValueError('Expected two firmware roles')
        result['status']='properties-checked-not-boot-validated'
    except (OSError,ValueError,KeyError) as exc:
        result.update(status='blocked',error=str(exc))
        raise
    finally:
        atomic_json(destination,result)
    return result


if __name__=='__main__':
    print(json.dumps(inspect(Path(sys.argv[1]).resolve()),indent=2))
