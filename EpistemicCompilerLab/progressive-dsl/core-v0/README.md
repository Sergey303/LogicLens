# Experimental Epistemic DSL core v0

This directory consolidates the already-tested semantic ideas from DSL-A, DSL-B, DSL-C and DSL-D2 behind one deterministic Python reference boundary.

It is a follow-on engineering artifact, not a replacement for the frozen progressive benchmark and not confirmatory evidence for WP-003 / ENG-155.

## Preserved distinctions

- support, oppose, unknown and conflict remain distinct;
- a logical rule derives only its declared head stance when its body is satisfied;
- bounded numeric observations abstain when a threshold crosses the bounds;
- dependent reports are averaged inside a dependency group;
- independent groups are combined cumulatively;
- conflict remains separate from uncertainty;
- the weak model never performs epistemic arithmetic.

## CTO-course smoke contract

The frozen six-case tranche checks:

1. supported CTO technology-strategy ownership;
2. unknown Product Manager backlog ownership;
3. derived CTO risk-escalation obligation from two supported premises;
4. abstention when an availability interval crosses a threshold;
5. duplicate reports inside one dependency group;
6. equivalent reports from independent groups.

Run from any PowerShell location through the repository launcher:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' progressive-core-tests
```
