# DSL-C0 Codex ablation result — 2026-08-05

## Status

The management numeric pilot completed successfully with 9 frozen cases, 3 conditions and 27 Codex calls.

- LogicLens checkout: `39fbd24`
- DSL-C package: `sha256:b8b286c5013e851892b8ba9db8802af7cf4c721fe063daa90fc11cd78aa52d05`
- Frozen cases: `sha256:8473bfc8dfbe258045d2f90c59606acd49e97dfffbae7e3af671656a0cc55dd0`
- Frozen observations: `sha256:8e7f6e0c6d0ecfab5074a7f4b4140b79ff1fab48cd8fd5425fd62a15c815b8ae`
- Model selection: account default
- Repetitions: 1

## Aggregate result

| Condition | Task status accuracy | Condition safety | Numeric values exact | Probability-policy safety | Mean latency |
|---|---:|---:|---:|---:|---:|
| Direct | 4/9 = 44.4% | 9/9 = 100% | n/a | 9/9 = 100% | 10.42 s |
| Raw observation | 9/9 = 100% | 9/9 = 100% | 9/9 = 100% | 9/9 = 100% | 15.29 s |
| Verified DSL-C | 9/9 = 100% | 9/9 = 100% | 9/9 = 100% | 9/9 = 100% | 12.37 s |

The verified frame was about 2.92 seconds faster on mean latency than Raw in this single run. This is descriptive pilot evidence, not a population estimate.

## Main interpretation

The pilot does **not** establish an accuracy advantage of the deterministic numerical kernel over a strong Codex model on these nine simple cases. Once Raw received the private point, interval or normal observation, it independently produced the same status and normalized values as Verified DSL-C in all cases.

The supported conclusions are narrower:

1. Direct preserved epistemic safety when private measurements were unavailable.
2. Raw Codex correctly handled the current unit conversions, inclusive ranges, threshold-crossing intervals and the normal-distribution abstention case.
3. Verified DSL-C produced independently checked deterministic frames and reduced renderer latency relative to Raw in this run.
4. The current cases have a ceiling effect for account-default Codex. Harder numerical strata are required before claiming an accuracy contribution from execution.

## Scorer finding

Two aggregate fields must not be treated as scientific quality metrics in their current form.

### `interpretationFlagsExactRate`

Codex often added the semantically correct flag `inclusive-range` to the required flags. Exact list equality therefore marked correct richer interpretations as failures. Future scorers must use:

- required flags as a subset;
- forbidden flags as a separate check;
- accepted alternatives where wording differs but semantics is equivalent.

### `warningsExactRate` for Raw

Raw did not receive internal warning identifiers and returned natural-language warnings. Comparing those strings to verified warning IDs makes `0%` expected by construction. The Raw condition should instead be scored on semantic obligations, not identifier transport.

## Consequence for DSL-D0

DSL-D0 must use contrast pairs that cannot be solved from a single scalar:

- equal projected probability with different uncertainty;
- equal `b,d,u` with different base rates;
- equal projection with different conflict;
- evidence-dominant versus prior-dominant support;
- high uncertainty requiring abstention;
- explicit refutation;
- answer-level opinion produced from declared evidence counts;
- missing-opinion control.

The experimental conditions are:

1. Direct;
2. Scalar projected probability only;
3. Raw `b,d,u,a`;
4. Verified DSL-D opinion frame.

This separates information availability, scalar compression loss, raw opinion interpretation and verified policy execution.

## Claim boundary

This pilot must not be used to claim that DSL-C improves accuracy over Raw. It supports reproducibility, explicit interval semantics, arithmetic auditability and a latency hypothesis that requires repeated runs.
