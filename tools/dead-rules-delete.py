#!/usr/bin/env python3
"""dead-rules-delete.py — remove the rules css-coverage proved dead, conservatively.

WHY (2026-09-13, architecture review #3). Once css-coverage learned to look inside @layer it
found 449 rules that match nothing on any page at either width, triple-confirmed. Dead code with
a live instrument saying "clean" had hidden them for a day. This deletes them from css/site/ —
but not blindly:
  - rules on INTERACTION states (:hover, :focus*, :active, :checked, [aria-*], [data-*], :open…)
    stay, because coverage reads the loaded page and cannot see a state a reader creates;
  - rules whose class or id is named in any script stay, because a script can add the class
    after load (2 tonight: .rl-ghost, .rl-ghost--press);
  - only a rule whose selector is EXACTLY a report entry is removed; compound siblings stay.
Input: a JSON list of selectors (the filtered plan). Dry by default; --apply writes and rebuilds.
PROOF is external: render-census + pixel-census before/after, css-parse-check, journey-check
and interaction-state-check (the latter two exercise states coverage cannot).
CANNOT SEE: a class added by a script that builds its name from pieces, or a page not in the
classic set (the book is out of scope and untouched).
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sorted(glob.glob(os.path.join(ROOT, 'css', 'site', '0*.css')))


def main():
    plan = json.load(open(sys.argv[1]))
    apply = '--apply' in sys.argv
    want = {}
    for s in plan: want[s] = want.get(s, 0) + 1
    removed, log = 0, []
    for f in SRC:
        s = open(f, encoding='utf-8').read()
        blank = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), s, flags=re.S)
        out, i = [], 0
        for m in re.finditer(r'(?<![\w\-.#:>+~\[\]()\s])?(?:^|(?<=[;{}\n]))\s*([^{}@;][^{};]*?)\s*\{([^{}]*)\}', blank, flags=re.M):
            sel = re.sub(r'\s+', ' ', m.group(1).strip())
            if want.get(sel, 0) > 0:
                want[sel] -= 1
                out.append(s[i:m.start()]); i = m.end(); removed += 1; log.append((os.path.basename(f), sel))
        out.append(s[i:])
        if apply and removed: open(f, 'w', encoding='utf-8').write(''.join(out))
    left = sum(v for v in want.values() if v > 0)
    print(f'{removed} rule(s) {"removed" if apply else "would be removed"}; {left} plan entr(ies) not found as exact selectors (left alone)')
    for f, sel in log[:12]: print(f'   {f}: {sel[:70]}')
    if apply:
        os.system(f'python3 {os.path.join(ROOT, "tools", "build-css.py")}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
