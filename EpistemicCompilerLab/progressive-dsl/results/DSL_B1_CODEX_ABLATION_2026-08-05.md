# DSL-B1 Codex ablation result — 2026-08-05

## Status

The non-guessable management tranche completed successfully with 6 frozen cases, 3 conditions and 18 Codex calls.

- LogicLens checkout before the run: `7ff5b108d42a7ed082aebdf0fae0ad1b60402599`
- DSL-A package: `sha256:7a8b529a9acde057ee667a3b3862e1db1006cc278959e92d213a25d337ea8e70`
- DSL-B1 package: `sha256:125b428e728f0b581cf5890ebee4e7727d294fa3679edaa59de578128850d881`
- Frozen cases, canonical UTF-8/LF: `sha256:83f5f582aaf49e49690c64a730335ac8dae45f40e5ed92d1224f5562b6aae552`
- Frozen rules, canonical UTF-8/LF: `sha256:828c4cb274cc48a7149ea8138c9c0a67131f550e46934f9439c73de92400b7eb`
- Model selection: account default
- Repetitions: 1

## Aggregate result

| Condition | Task status accuracy | Condition status accuracy | Condition abstention accuracy | Frame status accuracy | Evidence exact rate | Mean proof-node recall | Mean warning recall | Mean latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Direct | 1/6 = 16.7% | 6/6 = 100% | 6/6 = 100% | n/a | n/a | n/a | n/a | 12.45 s |
| Gold DSL-A | 1/6 = 16.7% | 6/6 = 100% | 6/6 = 100% | 6/6 = 100% | 6/6 = 100% | n/a | 100% | 11.82 s |
| Gold DSL-B1 | 6/6 = 100% | 6/6 = 100% | 6/6 = 100% | 6/6 = 100% | 6/6 = 100% | 100% | 100% | 11.22 s |

No fabricated evidence IDs or proof-node IDs were observed.

## Interpretation

This tranche establishes two different desirable behaviours rather than treating one score as sufficient.

1. Without the closed Northstar policy, Direct Codex abstained in all six cases. It therefore had low private-policy task accuracy but perfect condition safety. The experiment must not reward accidental guessing of unavailable policy facts.
2. DSL-A also preserved `unknown` correctly because it could not represent the new policy derivations.
3. With DSL-B1, Codex used the verified frame correctly for `supported`, `refuted`, `conflicting`, `unknown`, `all`, `any`, a two-hop proof and `notExplicit`.
4. The DSL-B1 condition improved private-policy task status accuracy from 16.7% to 100% without increasing mean latency relative to the two controls in this single run.

This is evidence for the usefulness of verified local knowledge and formal derivation. It is not yet an estimate of population-level effect size: the tranche is small and has one repetition.

## Important semantic limitation

Exact warning transport and proof-node recall do not prove complete semantic understanding.

In the `northstar-team-health-not-explicit` answer, Codex copied `not-explicit-premise-used`, but the prose did not clearly explain both required consequences:

- absence of explicit opposition is not positive evidence;
- the derived conclusion is non-monotonic and can change when explicit oppose evidence is added.

The response also used language close to transferring “responsibility”, while the formal predicate was `may_delegate`. Future evaluators must score semantic obligations in the natural-language answer, not only identifier fidelity.

## Consequence for the next level

DSL-C should introduce typed observations and deterministic numerical kernels while preserving the same experimental discipline:

- separate information availability from computation quality;
- retain intervals instead of collapsing them to point values;
- verify allowlisted unit conversions;
- return `unknown` when a bounded observation crosses a threshold;
- return a descriptive normal observation without converting it into a strict decision unless an explicit probabilistic policy is supplied;
- score semantic interpretation separately from frame copying.
