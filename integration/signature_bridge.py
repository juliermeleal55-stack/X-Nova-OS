#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Restricted certificate bridge: exact package AND exact preinstalled path.

Scanning/certificate-comparison integration is derived from ImpulseROM's
GPLv3 scoped-platform patch (pinned in manifests/impulse-ui9-audit.json).
This module does not sign APKs or grant trust to data-app updates.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from smali_paths import resolve

ROOT=Path(__file__).resolve().parent
OWNER='Lcom/android/server/pm/ScanPackageUtils;'
ARG='Lcom/android/internal/pm/parsing/pkg/ParsedPackage;'
MARKER='CONFIG_CUSTOM_PLATFORM_SIGNATURE'


def policy():
    data=json.loads((ROOT/'signature_policy.json').read_text())
    if not data:raise ValueError('Empty signature policy')
    seen=set()
    for package,paths in data.items():
        if not re.fullmatch(r'[a-zA-Z0-9_.]+',package) or not paths:raise ValueError('Invalid signature package')
        for path in paths:
            if not re.fullmatch(r'/(?:system/|system_ext/)[a-zA-Z0-9_/.-]+\.apk',path) or '..' in Path(path).parts or path in seen:raise ValueError('Invalid/duplicate signature path')
            seen.add(path)
    return data


def allowed(package,path):
    """Reference predicate for tests; same cases as the emitted smali."""
    return any(path in (p,str(Path(p).parent)) for p in policy().get(package,[]))


def allow_method():
    lines=[f'.method public static isAllowedCustomPlatformPackage({ARG})Z','    .locals 3',
      f'    invoke-interface {{p0}}, {ARG}->getPackageName()Ljava/lang/String;','    move-result-object v0',
      f'    invoke-interface {{p0}}, {ARG}->getPath()Ljava/lang/String;','    move-result-object v1']
    for i,(package,paths) in enumerate(policy().items()):
        lines += [f'    const-string v2, "{package}"','    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z','    move-result v2',f'    if-eqz v2, :package_{i}']
        for path in dict.fromkeys(p for apk in paths for p in (apk,str(Path(apk).parent))):
            lines += [f'    const-string v2, "{path}"','    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z','    move-result v2','    if-nez v2, :allowed']
        lines += ['    goto/32 :denied',f'    :package_{i}']
    lines += ['    :denied','    const/4 v0, 0x0','    return v0','    :allowed','    const/4 v0, 0x1','    return v0','.end method']
    return '\n'.join(lines)+'\n'


def method(text,signature):
    matches=re.findall(r'(?ms)^\.method [^\n]* '+re.escape(signature)+r'\n.*?^\.end method[^\n]*',text)
    if len(matches)!=1:raise ValueError('Missing/ambiguous signature method '+signature)
    return matches[0]


def normalized(text):return '\n'.join(line.strip() for line in text.splitlines() if line.strip())


def certificate(pem):
    data=subprocess.run(['openssl','x509','-in',str(pem),'-outform','DER'],check=True,capture_output=True).stdout
    if not data:raise ValueError('Empty platform certificate')
    return data.hex(),hashlib.sha256(data).hexdigest()


def validate(decoded,cert):
    scan=resolve(decoded,'smali_classes2/com/android/server/pm/ScanPackageUtils.smali')
    install=resolve(decoded,'smali_classes2/com/android/server/pm/InstallPackageHelper.smali')
    text=scan.read_text()
    expected=(ROOT/'platform_signature_methods.smali').read_text().replace(MARKER,cert)
    expected=allow_method()+'\n'+expected
    for signature in (f'isAllowedCustomPlatformPackage({ARG})Z',f'isSignedWithCustomPlatformKey({ARG})Z',f'setCustomSignatures({ARG}Lcom/android/server/pm/pkg/AndroidPackage;)V'):
        if normalized(method(text,signature))!=normalized(method(expected,signature)):raise ValueError('Signature bridge contract differs: '+signature)
    if len(re.findall(r'(?m)^\s*invoke-static \{[^}\n]+\}, '+re.escape(f'{OWNER}->setCustomSignatures({ARG}Lcom/android/server/pm/pkg/AndroidPackage;)V'),install.read_text()))!=2:raise ValueError('Missing/duplicate package-scan bridge callers')
    apply_policy=method(text,f'applyPolicy({ARG}ILcom/android/server/pm/pkg/AndroidPackage;Z)V')
    policy_call=f'{OWNER}->isSignedWithCustomPlatformKey({ARG})Z'
    if apply_policy.count(policy_call)!=1 or len(re.findall(r'(?m)^\s*invoke-static \{[^}\n]+\}, '+re.escape(policy_call),apply_policy))!=1:raise ValueError('Missing/duplicate/nonstatic platform-key policy call')
    return scan,text


def configure(decoded,pem,receipt):
    hexcert,digest=certificate(pem)
    scan=resolve(decoded,'smali_classes2/com/android/server/pm/ScanPackageUtils.smali')
    old=scan.read_text()
    if old.count(MARKER)!=1 or 'PUT SIGNATURE HERE' in old:raise ValueError('Expected exactly one new certificate marker; patch may have failed')
    # Validate every bridge contract BEFORE changing any file.
    validate(decoded,MARKER)
    text=old.replace(MARKER,hexcert)
    receipt.parent.mkdir(parents=True,exist_ok=True)
    record=dict(status='configured',certificate_sha256=digest,policy_sha256=hashlib.sha256((ROOT/'signature_policy.json').read_bytes()).hexdigest(),packages=list(policy()),scope='Exact preinstalled package/path and ROM certificate; NOT runtime/boot validation')
    scan.write_text(text)
    try:
        validate(decoded,hexcert)
        receipt.write_text(json.dumps(record,indent=2)+'\n')
    except Exception:
        scan.write_text(old);receipt.unlink(missing_ok=True);raise
    return record


def verify(decoded,pem,receipt):
    hexcert,digest=certificate(pem);record=json.loads(receipt.read_text())
    if record.get('status')!='configured' or record.get('certificate_sha256')!=digest or record.get('policy_sha256')!=hashlib.sha256((ROOT/'signature_policy.json').read_bytes()).hexdigest():raise ValueError('Signature receipt/certificate/policy mismatch')
    validate(decoded,hexcert)
    return record


if __name__=='__main__':
    try:
        action=sys.argv[1]
        if action not in ('configure','verify'):raise ValueError('Unknown signature operation')
        result=globals()[action](*(Path(p) for p in sys.argv[2:5]))
        print('Scoped platform signature bridge: '+result['status']+'; runtime not validated')
    except (OSError,ValueError,subprocess.SubprocessError) as exc:
        print('Signature bridge blocked: '+str(exc),file=sys.stderr);sys.exit(1)
