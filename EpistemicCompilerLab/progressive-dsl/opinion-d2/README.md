# Epistemic DSL-D2 — dependency-aware evidence fusion pilot

Linear work package: `ENG-187`.

DSL-D2 is a separate pilot extension of the opinion layer. It does not modify the strict epistemic benchmark and is not confirmatory evidence for the TMLR flagship claim.

## Research question

> Does explicit dependency metadata prevent duplicated evidence from being counted as independent corroboration?

The pilot uses an exact, declared policy:

- average evidence counts inside one `dependencyGroup`;
- cumulatively sum the resulting group-level counts across different groups;
- fail closed when dependency metadata or compatible base rates are missing;
- preserve conflict separately from uncertainty;
- perform all arithmetic with exact rational values.

This policy is intentionally local to D2. Dependency labels are asserted metadata, not proof that real sources are independent.

## Opinion mapping

With exact fused positive evidence `R`, negative evidence `S`, prior weight `W=2` and base rate `a`:

```text
b = R/(R+S+W)
d = S/(R+S+W)
u = W/(R+S+W)
p = b + a*u
conflict = 2*min(R,S)/(R+S)
```

The ordered D0/D1 decision policy is retained.

## Conditions

1. `metadata_absent` — dependency groups are hidden; multiple reports must not be fused.
2. `naive_independent` — every report is explicitly but incorrectly assumed independent.
3. `raw_declared` — reports, groups and the D2 policy are available; Codex computes the result.
4. `verified` — the exact operator plan, fused opinion and allowed conclusion are authoritative.

## Frozen cases

The 11-case tranche includes one report, duplicated and independent reports, mixed dependency groups, dependent and independent conflicts, missing metadata, incompatible base rates, an answer-level profile and independent refutation.

The key pair contains identical exact evidence counts. Only the dependency groups differ:

```text
same group       -> average    -> qualified_uncertain
different groups -> cumulative -> assert_with_evidence
```

Frozen hashes:

```text
reports: sha256:e0b8f561ba45eafe1d12ce3278c46edcf700356b02f674246ac93ed6e7b41c91
cases:   sha256:3e82d4e2348826a034946bd7f00c042ba706f161cf1b01b9bf5f87beded2616f
```

## Corrected semantic fields

D2 avoids the ambiguous D1 fields:

- `opinionSubjectLevel` is the subject of the opinion: `claim` or `answer`;
- operator plan is explicit;
- metadata completeness and base-rate compatibility are separate;
- implicit fusion remains forbidden.

## Expected offline pattern

| Condition | Distinguish dependent duplicate from independent corroboration |
|---|---|
| metadata absent | no; request metadata |
| naive independent | no; both are cumulatively amplified |
| raw declared | yes |
| verified | yes |

## Trust boundary

- Python uses `fractions.Fraction`;
- SWI-Prolog independently executes group averaging, cumulative group fusion and policy comparisons;
- the launcher runs frozen validation, 44 fake-provider calls and Python/SWI-Prolog verification before 44 real Codex calls;
- every raw response is stored before scoring.

## Run

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\run-progressive-management-codex-d2-ablation.ps1' `
  -LogicLensRoot 'D:\projects\ChatPilotGroup\LogicLens' `
  -Repetitions 1 `
  -TimeoutSeconds 300
```
