#!/usr/bin/env python3
"""ci-deps-check.py — does CI install what tools/ actually imports?

On 2026-08-30, asset-load-check.py began importing tools/cdp.py, which imports
`websocket`. The workflow step was called "Install Pillow" and installed exactly that.
So the Contrast gate died at IMPORT time on every single push for five days —
ModuleNotFoundError, before it checked one pixel — while the local hook stayed green
because this machine happens to have websocket-client installed.

Nobody could see it: job logs need admin rights, so the failure read only as
"Process completed with exit code 1". It looked like a failing check. It was a check
that never ran at all.

This reads the REAL imports with ast (a docstring that says "the eighteen gates" is not
an import, which a regex sweep reported as a module named `the`), maps them to their pip
names, and asserts every one appears in a workflow's pip install line.

Exit 0 clean · 1 a dependency CI would not have · 2 could not measure.
"""
import ast, glob, importlib.util, os, re, sys, sysconfig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# import name -> pip name, for the ones that differ
PIP_NAME = {'PIL': 'pillow', 'websocket': 'websocket-client', 'yaml': 'pyyaml',
            'bs4': 'beautifulsoup4', 'cv2': 'opencv-python'}
# modules that live in this repo, not on PyPI
# modules that live in tools/ itself, not on PyPI
LOCAL = {'cdp', 'gatelib'}

# sys.stdlib_module_names is 3.10+. On 3.9 the first version of this fell back to
# sys.builtin_module_names — about thirty C builtins — and duly reported that CI was
# missing `os` and `re`. Classify by where the module actually LIVES instead: anything
# resolving inside the stdlib directory (or built in / frozen) is standard, anything in
# site-packages is a dependency. Works on every version and needs no hardcoded list.
STDLIB_DIR = os.path.realpath(sysconfig.get_paths()['stdlib'])


def is_stdlib(mod):
    if mod in sys.builtin_module_names:
        return True
    if hasattr(sys, 'stdlib_module_names') and mod in sys.stdlib_module_names:
        return True
    try:
        spec = importlib.util.find_spec(mod)
    except (ImportError, ValueError, ModuleNotFoundError):
        return False
    if spec is None:
        return False                      # not installed anywhere — treat as a dependency
    origin = spec.origin or ''
    if origin in ('built-in', 'frozen'):
        return True
    return os.path.realpath(origin).startswith(STDLIB_DIR) and 'site-packages' not in origin

def imports_of(path):
    try:
        tree = ast.parse(open(path, encoding='utf-8').read(), filename=path)
    except SyntaxError as e:
        print(f'  UNMEASURED  {os.path.relpath(path, ROOT)} does not parse: {e}')
        return None
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found |= {a.name.split('.')[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split('.')[0])
    return found

needed, unparsed = {}, 0
for f in sorted(glob.glob(os.path.join(ROOT, 'tools', '*.py'))):
    got = imports_of(f)
    if got is None:
        unparsed += 1
        continue
    for mod in got:
        if mod in LOCAL or mod.startswith('_') or is_stdlib(mod):
            continue
        needed.setdefault(PIP_NAME.get(mod, mod), set()).add(os.path.basename(f))

workflows = sorted(glob.glob(os.path.join(ROOT, '.github', 'workflows', '*.yml')))
if not workflows:
    print('  UNMEASURED  no workflows found.\n\nThis is not a pass.')
    sys.exit(2)
installed = set()
for w in workflows:
    for line in open(w, encoding='utf-8'):
        if 'pip install' in line:
            installed |= set(re.findall(r'[A-Za-z0-9][A-Za-z0-9._-]+', line.split('pip install', 1)[1]))

# A hardcoded macOS path is the same defect as a missing package: the gate cannot run on
# the runner. cdp.py pinned /Applications/Google Chrome.app and ignored the $CHROME the
# workflow had been exporting all along, so the Contrast gate died with FileNotFoundError
# the moment the websocket-client fix finally let it import. Any tool naming a macOS-only
# path must also read the environment override.
mac_only = []
for f in sorted(glob.glob(os.path.join(ROOT, 'tools', '*.py'))):
    src = open(f, encoding='utf-8').read()
    if '/Applications/' not in src:
        continue
    # Match the CALL, not a closing paren: cta-viewport-check.py writes
    # os.environ.get("CHROME", "<default>") and the first version of this rule
    # reported it as mac-only. A detector that only knows one spelling of the
    # correct code invents defects.
    if 'environ.get("CHROME"' in src or "environ.get('CHROME'" in src:
        continue
    mac_only.append(os.path.basename(f))
for name in mac_only:
    print(f'  MAC-ONLY PATH  {name}\n                 names /Applications/... and never reads $CHROME — '
          f'cannot run on a Linux runner')

missing = {p: v for p, v in needed.items() if p not in installed}
for pkg, users in sorted(missing.items()):
    print(f'  MISSING IN CI  {pkg}\n                 imported by {", ".join(sorted(users))}')
if missing or mac_only:
    print(f'\n{len(missing)} missing package(s) and {len(mac_only)} mac-only path(s). '
          f'A gate that cannot import or cannot launch is a gate that never ran.')
    sys.exit(1)
if unparsed:
    print(f'\n{unparsed} tool(s) could not be parsed. This is not a full pass.')
    sys.exit(2)
print(f'{len(needed)} third-party package(s) imported by tools/: '
      f'{", ".join(sorted(needed))} — all installed by CI.')
print('CANNOT SEE: a package imported inside a function or a try/except, a version')
print('mismatch, or a dependency of a dependency.')
