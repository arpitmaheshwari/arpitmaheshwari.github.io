# Ember — a design system as a Claude plugin

This is the design system behind [arpitmaheshwari.com](https://arpitmaheshwari.com), packaged so
Claude produces work that is already on-system instead of work someone has to correct afterwards.

It exists because of a claim on that site: at Talon Outdoor I unified six products under one
design system, then encoded it as a Claude plugin and shipped it across the engineering org —
and a second one at Sahaj. Those two are client-confidential. This one is the same practice,
built on a system I can publish, so the claim can be inspected rather than taken on faith.

## Install

```
/plugin marketplace add arpitmaheshwari/arpitmaheshwari.github.io
/plugin install ember-design-system
```

Or point Claude Code at a local checkout of the `plugin/` directory.

## What's inside

| Skill | What it does |
|---|---|
| `ember-design-system` | The tokens, type scale, spacing grid and component grammar — with the rules that are not obvious from the values |
| `ship-gates` | The ten checks that decide whether a change ships, and the discipline that makes them worth trusting |

## The idea worth stealing, if you take nothing else

A design system that only lives in a Figma library gets applied by whoever remembers it. A design
system encoded as rules a machine reads gets applied every time — and the moment it is wrong, it
is wrong *visibly and in one place*, which is the only kind of wrong you can fix.

MIT licensed. The system is mine; the method is yours.
