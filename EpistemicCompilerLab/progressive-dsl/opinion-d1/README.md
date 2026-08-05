# Epistemic DSL-D1 — exact-rational boundary pilot

Linear work package: `ENG-186`.

DSL-D1 is a separate pilot extension of DSL-D0. It does not modify the strict epistemic benchmark and is not confirmatory evidence for the TMLR flagship claim.

## Research question

> Can rounded decimal opinions change a policy decision near an exact boundary, and does an exact rational representation preserve the intended result?

DSL-D0 showed that a complete Raw opinion and a Verified opinion frame produced the same conclusion on 9/9 simple cases, while Scalar lost uncertainty, base-rate and conflict information. It also exposed a precision issue: rounded masses could produce `p=0.7500005` while the exact rational profile was `p=3/4`.

## Conditions

1. `scalar` — only rounded projected probability;
2. `rounded` — rounded decimal `b,d,u,a,conflict`, no ready conclusion;
3. `exact` — numerator/denominator values, no ready conclusion;
4. `verified` — exact and rounded values plus authoritative exact policy result.

## Policy

The policy is the same ordered D0 policy, but all exact decisions are made with rational arithmetic:

1. conflict `>= 1/2`;
2. uncertainty `>= 1/2`;
3. supported if `p >= 3/4`, `b >= 1/2`, `u <= 1/4`;
4. refuted if `p <= 1/4`, `d >= 1/2`, `u <= 1/4`;
5. prior-sensitive if `p >= 13/20`, `b < 1/2`, `u < 1/2`;
6. otherwise qualified uncertainty.

`withholdsAssertiveDecision` replaces the ambiguous generic `abstain` field. Conflict reporting and qualified uncertainty both withhold binary assertion/refutation while still producing a user-facing message.

## Frozen boundary pairs

The tranche contains 11 cases:

- `p` immediately below and above `3/4`, both rounded to `0.75`;
- `u` immediately below and above `1/2`, both rounded to `0.50`;
- conflict immediately below and above `1/2`, both rounded to `0.50`;
- `b` immediately below and above `1/2`, both rounded to `0.50`;
- repeating rational answer-level aggregation;
- lexical decimal control;
- rounded-only missing-exactness control.

Frozen hashes:

```text
opinions: sha256:efa8664833f621bfca077c26f73c926782b3275be9b369678b47b0da8d359e6f
cases:    sha256:f2efb45fabb580d76e30ae376b8740478fbb3b63b3d11b375954965eac222947
```

## Expected causal pattern

The four exact pairs have different exact conclusions but identical rounded conclusions.

Therefore:

| Condition | Distinguish exact boundary pairs |
|---|---|
| Scalar | no |
| Rounded | no |
| Exact | yes |
| Verified | yes |

The primary pilot metric is exact boundary preservation, not lexical string equality.

## Scoring

The scorer separates:

- numeric equality from canonical lexical equality;
- supplied-number transport from derived projection arithmetic;
- exact fraction transport;
- exact boundary preservation;
- rounded and exact invariant interpretation;
- required warning IDs as a subset;
- probability/fusion safety;
- typed withholding behaviour.

## Trust boundary

- Python uses `fractions.Fraction`;
- SWI-Prolog independently executes integer cross-multiplication;
- exact comparison occurs before decimal rendering;
- rounding mode is declared as half-even;
- no implicit fusion is performed;
- exact source absence remains open-world and requests exact input.

## Run

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\run-progressive-management-codex-d1-ablation.ps1' `
  -LogicLensRoot 'D:\projects\ChatPilotGroup\LogicLens' `
  -Repetitions 1 `
  -TimeoutSeconds 300
```

The launcher performs frozen contract validation, 44 offline fake-provider calls, Python/SWI-Prolog cross-verification and then 44 real Codex calls.
