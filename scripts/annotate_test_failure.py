#!/usr/bin/env python3
"""Bounded CI failure tail, retrievable through the Checks API without log blobs."""
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(errors='replace')
start = text.rfind('\n======================================================================\nFAIL:')
if start < 0:
    start = text.rfind('\n======================================================================\nERROR:')
text = text[start:] if start >= 0 else text[-5600:]
text = text[-5600:]
for offset in range(0, len(text), 2800):
    chunk = text[offset:offset + 2800].replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
    print('::error title=Integration test failure::' + chunk)
