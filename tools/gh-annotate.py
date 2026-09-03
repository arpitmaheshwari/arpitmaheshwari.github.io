#!/usr/bin/env python3
"""gh-annotate.py — turn a failed step's tail into a GitHub check annotation.

GitHub job logs need admin rights to read (the API returns 403) and job summaries are
not exposed through the API at all. Check ANNOTATIONS are public. So when a gate fails
in CI, the only way anyone without admin can learn WHY is for the step to emit its own
output as an ::error:: workflow command.

This exists because the Contrast gate failed on every push from 2026-08-30 to 2026-09-04
and the only visible detail was "Process completed with exit code 1".

    python3 tools/gh-annotate.py <file> "<title>" [tail_lines]
"""
import io, sys

path = sys.argv[1]
title = sys.argv[2] if len(sys.argv) > 2 else 'step failed'
tail_n = int(sys.argv[3]) if len(sys.argv) > 3 else 25

try:
    lines = io.open(path, encoding='utf-8', errors='replace').read().splitlines()
except OSError as e:
    print(f'::error title={title}::could not read {path}: {e}')
    sys.exit(0)

# Workflow commands are one line: newlines must be %0A, and % itself escaped first.
body = '%0A'.join(l.replace('%', '%25').replace('\r', '') for l in lines[-tail_n:])
print(f'::error title={title}::{body or "(no output captured)"}')
