#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fail-closed, review-only adaptation of OneROM's narrow search-index guard."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

EXPECTED_CLASS = (
    'Lcom/android/settings/intelligence/search/indexing/DevicePolicyResourcesUtils;'
)
LABEL = ':xnova_s10_policy_resource_present'
GET_RESOURCE_ID = re.compile(
    r'^\s*invoke-virtual\s+\{([^}]+)\}, '
    r'Landroid/content/res/TypedArray;->getResourceId\(II\)I\s*$'
)
GET_RESOURCE_ENTRY = re.compile(
    r'^\s*invoke-virtual\s+\{([^}]+)\}, '
    r'Landroid/content/res/Resources;->getResourceEntryName\(I\)Ljava/lang/String;\s*$'
)
MOVE_RESULT = re.compile(r'^\s*move-result\s+([vp][0-9]+)\s*$')
DEFAULT_MINUS_ONE = re.compile(
    r'^\s*const(?:/4|/16)?\s+([vp][0-9]+),\s*(-0x1|-1|0xffffffff)\s*$', re.I
)
REGISTER = re.compile(r'^[vp][0-9]+$')


class CandidateMismatch(ValueError):
    """The donor smali does not prove the narrow transformation's assumptions."""


def _significant(lines: list[str], start: int, end: int) -> list[int]:
    return [i for i in range(start, end)
            if lines[i].strip() and not lines[i].lstrip().startswith('#')]


def _registers(value: str) -> list[str]:
    result = [part.strip() for part in value.split(',')]
    if not result or any(not REGISTER.fullmatch(part) for part in result):
        raise CandidateMismatch('Only explicit, non-range Smali register lists are accepted')
    return result


def _method_parameter_words(header: str) -> tuple[int, bool]:
    tokens = header.split()
    if not tokens or not tokens[0] == '.method' or not tokens[-1].endswith(')Z'):
        raise CandidateMismatch('Target method must return boolean (Z)')
    descriptor = tokens[-1]
    opening = descriptor.find('(')
    closing = descriptor.rfind(')')
    if opening < 0 or closing < opening:
        raise CandidateMismatch('Malformed target method descriptor')
    params = descriptor[opening + 1:closing]
    words = 0
    i = 0
    while i < len(params):
        if params[i] == '[':
            while i < len(params) and params[i] == '[':
                i += 1
            if i >= len(params):
                raise CandidateMismatch('Malformed array parameter')
            if params[i] == 'L':
                end = params.find(';', i)
                if end < 0:
                    raise CandidateMismatch('Malformed object parameter')
                i = end + 1
            else:
                i += 1
            words += 1
        elif params[i] == 'L':
            end = params.find(';', i)
            if end < 0:
                raise CandidateMismatch('Malformed object parameter')
            i = end + 1
            words += 1
        else:
            words += 2 if params[i] in 'JD' else 1
            i += 1
    is_static = 'static' in tokens[1:-1]
    return words + (0 if is_static else 1), is_static


def _boolean_register(lines: list[str], method_start: int, method_end: int,
                      header: str) -> str:
    parameter_words, _ = _method_parameter_words(header)
    directives = []
    for i in range(method_start + 1, method_end):
        match = re.fullmatch(r'\s*\.(locals|registers)\s+([0-9]+)\s*', lines[i].rstrip('\r\n'))
        if match:
            directives.append((match.group(1), int(match.group(2))))
    if len(directives) != 1:
        raise CandidateMismatch('Expected exactly one .locals or .registers directive')
    kind, amount = directives[0]
    if kind == 'locals':
        if amount > 0:
            return 'v0'
        total_registers = amount + parameter_words
    else:
        total_registers = amount
    if total_registers < parameter_words or parameter_words == 0:
        raise CandidateMismatch('No safe low register is available for the false return')
    p0_index = total_registers - parameter_words
    if p0_index > 15:
        raise CandidateMismatch('p0 is outside const/4 range and there are no local registers')
    return 'p0'


def adapt_text(text: str) -> str:
    """Insert a guard only when the exact donor register contract is proven."""
    if '\r' in text.replace('\r\n', ''):
        raise CandidateMismatch('Mixed line endings are not supported')
    lines = text.splitlines(keepends=True)
    class_headers = [line.strip().split()[-1] for line in lines
                     if line.strip().startswith('.class ')]
    if class_headers != [EXPECTED_CLASS]:
        raise CandidateMismatch('Input must be the exact DevicePolicyResourcesUtils class')
    if LABEL in text or ':s10_policy_resource_present' in text:
        raise CandidateMismatch('A prior candidate/upstream guard is already present')

    method_ranges = []
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith('.method '):
            start = i
            end = next((j for j in range(i + 1, len(lines))
                        if lines[j].strip() == '.end method'), None)
            if end is None:
                raise CandidateMismatch('Unterminated Smali method')
            method_ranges.append((start, end))
            i = end + 1
        else:
            i += 1

    candidates = []
    for start, end in method_ranges:
        for line_index in range(start + 1, end):
            if GET_RESOURCE_ENTRY.fullmatch(lines[line_index].rstrip('\r\n')):
                candidates.append((start, end, line_index))
    if len(candidates) != 1:
        raise CandidateMismatch('Expected exactly one getResourceEntryName(I) call in the class')

    method_start, method_end, entry_index = candidates[0]
    header = lines[method_start].strip()
    significant = _significant(lines, method_start + 1, method_end)
    try:
        entry_position = significant.index(entry_index)
    except ValueError as exc:
        raise CandidateMismatch('Resource lookup is not an executable instruction') from exc
    if entry_position < 2:
        raise CandidateMismatch('Resource lookup lacks the expected getResourceId result')

    entry_registers = _registers(
        GET_RESOURCE_ENTRY.fullmatch(lines[entry_index].rstrip('\r\n')).group(1)
    )
    if len(entry_registers) != 2:
        raise CandidateMismatch('Expected receiver and resource-ID registers for the lookup')
    result_index = significant[entry_position - 1]
    result_match = MOVE_RESULT.fullmatch(lines[result_index].rstrip('\r\n'))
    if not result_match or result_match.group(1) != entry_registers[1]:
        raise CandidateMismatch('Resource lookup must consume the immediately preceding int result')

    id_call_index = significant[entry_position - 2]
    id_match = GET_RESOURCE_ID.fullmatch(lines[id_call_index].rstrip('\r\n'))
    if not id_match:
        raise CandidateMismatch('Expected getResourceId(II)I immediately before move-result')
    id_registers = _registers(id_match.group(1))
    if len(id_registers) != 3 or id_registers[2] == result_match.group(1):
        raise CandidateMismatch('Expected receiver/index/default registers with a preserved sentinel')
    if id_registers[2] == id_registers[1]:
        raise CandidateMismatch('Index and default registers must be distinct')

    id_calls = [i for i in significant if '->getResourceId(II)I' in lines[i]]
    if id_calls != [id_call_index]:
        raise CandidateMismatch('Ambiguous getResourceId calls in the target method')
    if entry_position < 3:
        raise CandidateMismatch('No explicit default sentinel before getResourceId')
    default_const_index = significant[entry_position - 3]
    const_match = DEFAULT_MINUS_ONE.fullmatch(lines[default_const_index].rstrip('\r\n'))
    if not const_match or const_match.group(1) != id_registers[2]:
        raise CandidateMismatch('The getResourceId default must be explicitly set to -1 immediately before the call')

    # The return register is local v0 when available, otherwise a low p0.
    # It is written only on the early-return branch, so live donor values on
    # the valid-resource path remain unchanged.
    return_register = _boolean_register(lines, method_start, method_end, header)
    indent = re.match(r'\s*', lines[result_index]).group(0)
    newline = '\r\n' if '\r\n' in text else '\n'
    addition = [
        f'{indent}if-ne {result_match.group(1)}, {id_registers[2]}, {LABEL}{newline}',
        newline,
        f'{indent}const/4 {return_register}, 0x0{newline}',
        f'{indent}return {return_register}{newline}',
        newline,
        f'{indent}{LABEL}{newline}',
    ]
    lines[result_index + 1:result_index + 1] = addition
    return ''.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='decoded donor Smali input (never overwritten)')
    parser.add_argument('output', type=Path, help='new candidate Smali output path')
    args = parser.parse_args()
    source = args.source
    output = args.output
    if source.is_symlink() or not source.is_file():
        parser.error('source must be a regular, non-symlink Smali file')
    if output.exists() or output.is_symlink():
        parser.error('output must not already exist; the tool never overwrites')
    if source.resolve() == output.resolve():
        parser.error('source and output must be distinct')
    try:
        transformed = adapt_text(source.read_text(encoding='utf-8'))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(transformed, encoding='utf-8')
    except (OSError, UnicodeError, CandidateMismatch) as exc:
        print(f'OneROM candidate adapter refused input: {exc}', file=sys.stderr)
        return 1
    print(f'Review candidate written (not build-integrated): {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
