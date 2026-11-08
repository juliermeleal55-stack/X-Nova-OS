# SPDX-License-Identifier: GPL-3.0-or-later
"""Narrow, hash-pinned equivalents of selected legacy patches; no fuzzy hunks."""
import hashlib
import json
from pathlib import Path
import re
from smali_paths import resolve

SPECS = Path(__file__).with_name('semantic_smali.json')


def method_return(text, signature, value, static, absent_if_unreferenced=False):
    expected={'null':'Ljava/lang/String;','true':'Z','false':'Z','void':'V'}.get(value)
    if expected is None or not signature.endswith(')'+expected):raise ValueError('Unexpected return contract')
    pattern=re.compile(r'(?ms)^(\.method ([^\n]* )?'+re.escape(signature)+r')\n(.*?)^\.end method[^\n]*')
    matches=list(pattern.finditer(text))
    if not matches and absent_if_unreferenced and value=='void' and signature=='setCallEndTonePlayStatus(Z)V' and 'setCallEndTonePlayStatus' not in text:
        return text  # The legacy patch's sole functional call is absent in this class.
    if len(matches)!=1:raise ValueError('Missing/ambiguous method '+signature)
    m=matches[0]; flags=m[1].split()
    if ('static' in flags)!=static or 'abstract' in flags or 'native' in flags:
        raise ValueError('Unexpected method modifiers '+signature)
    body=m[3]
    if '.param ' in body or body.count('.annotation')!=body.count('.end annotation'):
        raise ValueError('Unsupported parameter/annotation layout '+signature)
    annotations='\n'.join(re.findall(r'(?ms)^\s*\.annotation .*?^\s*\.end annotation\s*$',body))
    if value=='void':code='    .locals 0\n'+annotations+'\n    return-void\n'
    else:
        opcode='return-object' if value=='null' else 'return'
        constant='0x1' if value=='true' else '0x0'
        code=f'    .locals 1\n{annotations}\n    const/4 v0, {constant}\n\n    {opcode} v0\n'
    return text[:m.start()]+m[1]+'\n'+code+'.end method'+text[m.end():]


def method_instruction(text, signature, static, digest, old, new):
    """One instruction in an exact donor method; no register/label inference."""
    pattern=re.compile(r'(?ms)^\.method [^\n]* '+re.escape(signature)+r'\n.*?^\.end method[^\n]*')
    matches=list(pattern.finditer(text))
    if len(matches)!=1:raise ValueError('Missing/ambiguous instruction method '+signature)
    m=matches[0];body=m[0];flags=body.splitlines()[0].split()
    if ('static' in flags)!=static or 'native' in flags or 'abstract' in flags:raise ValueError('Unexpected instruction method modifiers')
    normalized='\n'.join(line.strip() for line in body.splitlines() if line.strip())
    if hashlib.sha256(normalized.encode()).hexdigest()!=digest:raise ValueError('Instruction method differs from inspected donor')
    if not all(re.fullmatch(r'move v[0-9]+, v[0-9]+',code) for code in (old,new)):raise ValueError('Unsupported instruction edit')
    lines=body.splitlines(keepends=True)
    positions=[i for i,line in enumerate(lines) if line.strip()==old]
    if len(positions)!=1:raise ValueError('Missing/ambiguous donor instruction')
    i=positions[0];lines[i]=lines[i].replace(old,new)
    return text[:m.start()]+''.join(lines)+text[m.end():]


def force_applock(text):
    matches=list(re.finditer(r'(?ms)^\.method [^\n]*<clinit>\(\)V\n.*?^\.end method',text))
    if len(matches)!=1:raise ValueError('Expected one CoreRune static initializer')
    m=matches[0];body=m[0]
    flags=body.splitlines()[0].split()
    if 'static' not in flags or 'constructor' not in flags or 'native' in flags or 'abstract' in flags:
        raise ValueError('Unexpected CoreRune initializer modifiers')
    locals_=list(re.finditer(r'(?m)^(\s*\.locals )([0-9]+)\s*$',body))
    if len(locals_)!=1 or int(locals_[0][2])>255:raise ValueError('Unsupported CoreRune local register budget')
    fields=('FW_SUPPORT_APPLOCK','FW_APPLOCK')
    if all(re.search(r'const/(?:4|16) (?P<r>v\d+), 0x1\s+sput-boolean (?P=r), Lcom/samsung/android/rune/CoreRune;->'+field+r':Z',body) for field in fields):
        return text
    register='v'+locals_[0][2]
    for field in ('FW_SUPPORT_APPLOCK','FW_APPLOCK'):
        pattern=re.compile(r'(?m)^\s*sput-boolean [vp]\d+, Lcom/samsung/android/rune/CoreRune;->'+field+r':Z\s*$')
        if len(list(pattern.finditer(body)))!=1:raise ValueError('Missing/ambiguous AppLock field '+field)
        body=pattern.sub('\n    const/16 '+register+', 0x1\n\n    sput-boolean '+register+', Lcom/samsung/android/rune/CoreRune;->'+field+':Z',body)
    body=re.sub(r'(?m)^(\s*\.locals )([0-9]+)\s*$',lambda x:x[1]+str(int(x[2])+1),body,count=1)
    return text[:m.start()]+body+text[m.end():]


def force_boolean_fields(text, fields):
    """Use a fresh local for pinned boolean stores, never donor register guesses."""
    headers=re.findall(r'(?m)^\.class[^\n]* (L[^\s]+;)\s*$',text)
    if len(headers)!=1 or not fields or any(type(v) is not bool for v in fields.values()):raise ValueError('Invalid boolean field contract')
    owner=headers[0]
    methods=list(re.finditer(r'(?ms)^\.method [^\n]*<clinit>\(\)V\n.*?^\.end method',text))
    if len(methods)!=1:raise ValueError('Expected one boolean static initializer')
    m=methods[0];body=m[0];flags=body.splitlines()[0].split()
    if 'static' not in flags or 'constructor' not in flags or 'native' in flags or 'abstract' in flags:raise ValueError('Unexpected boolean initializer modifiers')
    locals_=list(re.finditer(r'(?m)^(\s*\.locals )([0-9]+)\s*$',body))
    if len(locals_)!=1 or int(locals_[0][2])>255:raise ValueError('Unsupported boolean local register budget')
    patterns={}
    for field in fields:
        if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',field):raise ValueError('Unexpected boolean field name')
        declarations=re.findall(r'(?m)^\.field [^\n]* '+re.escape(field)+r':Z(?: = [^\n]+)?$',text)
        pattern=re.compile(r'(?m)^\s*sput-boolean [vp][0-9]+, '+re.escape(owner)+'->'+field+r':Z\s*$')
        if len(declarations)!=1 or len(list(pattern.finditer(body)))!=1:raise ValueError('Missing/ambiguous boolean field '+field)
        patterns[field]=pattern
    # Already-correct output remains stable on replay.
    if all(re.search(r'const/(?:4|16) (?P<r>v[0-9]+), '+('0x1' if value else '0x0')+r'\s+sput-boolean (?P=r), '+re.escape(owner)+'->'+field+r':Z',body) for field,value in fields.items()):return text
    register='v'+locals_[0][2]
    for field,value in fields.items():
        body=patterns[field].sub('\n    const/16 '+register+', '+('0x1' if value else '0x0')+'\n\n    sput-boolean '+register+', '+owner+'->'+field+':Z',body)
    body=re.sub(r'(?m)^(\s*\.locals )([0-9]+)\s*$',lambda x:x[1]+str(int(x[2])+1),body,count=1)
    return text[:m.start()]+body+text[m.end():]


def plan(workspace, decoded, patch):
    relative=str(patch.resolve().relative_to(workspace.resolve()))
    specs=json.loads(SPECS.read_text())
    spec=specs.get(relative)
    if spec is None:return None
    raw=patch.read_bytes()
    digest=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if digest!=spec['sha']:raise ValueError('Semantic patch differs from pinned upstream: '+relative)
    targets={}
    for item in spec['classes']:
        path=resolve(decoded,item['path']);text=path.read_text()
        if item.get('applock'):
            text=force_applock(text)
        elif 'booleans' in item:
            text=force_boolean_fields(text,item['booleans'])
        else:
            for change in item['methods']:
                if 'instruction' in change:
                    edit=change['instruction']
                    text=method_instruction(text,change['signature'],change['static'],edit['method_sha256'],edit['old'],edit['new'])
                else:
                    text=method_return(text,change['signature'],change['value'],change['static'],change.get('absent_if_unreferenced',False))
        targets[path]=text
    # Caller validates every class before committing any of them.
    return targets
