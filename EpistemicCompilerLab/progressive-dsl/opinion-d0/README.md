# Epistemic DSL-D0 — binomial opinion pilot

Linear work package: `ENG-185`.

DSL-D0 is a separate pilot layer. It does not modify the strict epistemic benchmark and is not confirmatory evidence for the TMLR flagship claim.

## Opinion

A binomial opinion is:

```text
ω = (b, d, u, a)
b + d + u = 1
p = b + a*u
```

- `b`: belief mass supported by evidence;
- `d`: disbelief mass supported by opposing evidence;
- `u`: uncommitted mass caused by insufficient evidence;
- `a`: base rate used to project uncertainty;
- `p`: projected probability, not a confidence score.

`conflictIndex` is deliberately separate from `u`.

## Source modes

- `direct-opinion`: `b,d,u,a` are supplied by an addressable source fixture;
- `evidence-counts`: the runtime computes `b,d,u,a` from positive/negative evidence counts and a declared prior weight;
- `missing`: no opinion is loaded and the runtime abstains.

For the answer-level fixture the proposition is explicitly `answer_correct(answer.executive-readiness-memo-v1)`. The profile does not claim that every sentence in the text is true. Its evidence-count aggregation policy is declared and no implicit fusion is performed.

## D0 policy

Policy rules are applied in order:

1. high conflict → report conflict;
2. high uncertainty → abstain;
3. strong evidence-dominant support → assert with profile;
4. strong evidence-dominant opposition → qualified refutation;
5. prior-sensitive support → qualify and warn;
6. otherwise → qualified uncertainty.

## Contrast pairs

The frozen pilot includes:

- equal projection `0.85`, different uncertainty;
- equal `b,d,u`, different base rates;
- equal projection `0.70`, different conflict;
- explicit refutation;
- computed answer-level opinion;
- missing-opinion control.

Frozen hashes:

```text
opinions: sha256:7da7d9209c506bce40040004a36041f58a81cf2031f22eaf44c4fa54cdfb48d2
cases:    sha256:018904bb2b5f8487a21ad0308ce3ea6131903ddd0b6c1ba07087ced98d11cb4d
```

## Leakage controls

- Direct questions do not contain projected probability, base-rate category, uncertainty category or conflict category.
- Internal case IDs are not sent to Codex; labels such as `prior-dominant` and `high-conflict` remain evaluator-only metadata.
- Scalar receives only the projected probability in addition to the neutral question.
- Raw receives the full opinion and conflict but no computed conclusion.
- Verified receives the complete runtime frame.

## Experiment

Four conditions are intentionally separated:

1. `direct`: no private opinion;
2. `scalar`: projected probability only;
3. `raw`: complete `b,d,u,a` and conflict, but no conclusion;
4. `verified`: complete runtime frame including allowed conclusion.

The main contrast is not simply “with versus without data”:

- Direct → Scalar measures scalar availability;
- Scalar → Raw measures information lost by scalar compression;
- Raw → Verified measures the value of deterministic policy execution.

## Run

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\run-progressive-management-codex-d0-ablation.ps1' `
  -LogicLensRoot 'D:\projects\ChatPilotGroup\LogicLens' `
  -Repetitions 1 `
  -TimeoutSeconds 300
```

The launcher runs fixture validation, an offline fake-provider contract, Python/SWI-Prolog cross-verification for all frames and then 36 Codex calls.
