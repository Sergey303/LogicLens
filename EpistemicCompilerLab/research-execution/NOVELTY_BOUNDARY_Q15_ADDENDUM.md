# WP-003 Q15 novelty-boundary addendum — 2026-08-11

Status: **producer remediation candidate; independent Research Program Architect re-review required**.

This addendum is append-only. It does not rewrite the previously frozen Q13/Q14 artifacts. For the current WP-003 producer candidate, read `NOVELTY_BOUNDARY.md` together with this file; where freshness/saturation language conflicts, this Q15 addendum is later and controlling.

## Why Q15 exists

Independent R3 found that the Q13/Q14 refresh still omitted several July/August 2026 works materially close to the expanded transfer ladder. Q15 therefore attacks six additional mechanism families: contract-grounded verified tool execution, typed executable operation languages with deterministic SQL/reference backends, frozen-SLM routing, small-model agent/tool/routing comparisons, explicit-state interacting-rule reasoning, and deterministic authoritative-state executability gating.

## New occupied territory

### ToolGate — verified state evolution and tool contracts

`RW-059` establishes an explicit typed symbolic state representing trusted world information, Hoare-style preconditions that gate tool invocation, and postconditions that gate whether tool results may update state through runtime verification.

Therefore the flagship may **not** claim novelty for:

- keeping a typed trusted state around an LLM agent;
- using formal pre/post conditions to gate tool calls;
- verifying tool results before committing them to trusted state;
- presenting runtime-verified state evolution as a new mechanism by itself.

ToolGate does not, on the reviewed primary-source evidence, provide the complete flagship causal profile: fixed-weight small renderer, supported/refuted/unknown/conflicting status contract, matched structure/no-conclusion/copying controls, and independent layer-specific oracle/scorer.

### Text2Mem — schema contracts, typed operations and deterministic execution

`RW-060` represents natural-language memory instructions as schema-based contracts with semantic invariants, parses validated schemas into typed operation objects, and executes them through a unified pipeline that includes a SQL reference backend. Its benchmark explicitly separates schema generation from backend execution.

Therefore the flagship may **not** claim novelty for:

- schema-contract → typed-operation compilation;
- deterministic execution of typed LLM-facing operations;
- using SQL as a conventional reference backend for an LLM-facing formal operation layer;
- separating planning/schema generation from execution fidelity as an evaluation idea.

This strengthens the role of ENG-197/ENG-199 as conventional falsification comparators rather than novel mechanisms.

### LatentGate and Rethinking Scale — frozen/small-model routing baselines

`RW-061` uses a frozen SLM backbone and a lightweight learned probe for routing among many agents. `RW-062` compares <10B open-source models under base, tool-equipped single-agent and routing-based multi-agent paradigms.

Therefore frozen-small-model routing and the broad claim that agent/tool scaffolding can improve small models are established territory. ENG-200 must be interpreted causally as a matched placement/routing contrast, not as a novelty claim for using a frozen small model with a router.

### Guidelines as Environments — explicit state for interacting and conflicting rules

`RW-063` builds an explicit evolving evidence state from guideline text and externalizes dependencies/conflicts among rules. Its transitions remain model-estimated rather than the deterministic strict-epistemic execution boundary proposed in the flagship.

Therefore explicit state for rule applicability/satisfaction/conflict is not itself novel. The surviving distinction must stay tied to the exact deterministic four-state contract and its causal placement/evaluation design.

### Don't Offer What Can't Be Done — authoritative-state executability gating

`RW-064` places a deterministic gate between semantic recall and final LLM skill selection. The gate evaluates hard-stop predicates against authoritative state and removes skills that cannot execute; the paper also reports counterfactual replay with all skills exposed.

Therefore the flagship may **not** claim novelty for deterministic authoritative-state gating before LLM routing/selection or for using counterfactual replay to show that gating changes model choices.

## Surviving candidate contribution after Q15

Q15 does **not** identify an exact prior work matching the complete seven-dimension flagship profile under the frozen strict-YES rule. The defensible candidate contribution remains deliberately narrow:

> A preregistered matched causal evaluation of **authoritative semantic-result placement** for fixed-weight small language models under a four-state strict epistemic contract, with structure/no-conclusion/answer-copying controls and an independently implemented layer-specific oracle/scorer.

This is a positive-comparison contribution, not a priority claim. Q15 strengthens the requirement that the manuscript directly distinguish the result from ToolGate, Text2Mem, SOP-Agent, PA-Tool, SIGIL, SkillSmith, conventional small-model tool/routing systems and the weight-adaptation literature.

## Q15 causal consequences for W0

1. **Trusted execution alone is not enough.** ToolGate and Text2Mem make verified/deterministic execution a strong conventional explanation.
2. **Typed interfaces alone are not enough.** Text2Mem and prior compiler/runtime work occupy typed executable contracts.
3. **Routing alone is not enough.** LatentGate, Rethinking Scale, SOP-Agent and deterministic executability gating occupy multiple routing mechanisms.
4. **Explicit rule state alone is not enough.** Guidelines as Environments already models interacting/conflicting rules through explicit evidence state.
5. The paper must win on the combined causal question it actually preregisters: where an authoritative four-state semantic result is placed and what obligations remain for the fixed small renderer, under matched controls and independent scoring.

## Saturation status

Q13/Q14 remain reproducible historical refresh rounds, but they are no longer the latest W0 freshness evidence. `Q15_SATURATION_ROUND_2026-08-11.csv` is the latest usable producer-side saturation round.

All six Q15 candidates are recorded in the Q15 screening and seven-dimension ledgers. None reaches five strict `YES` dimensions out of seven. This supports only current search-coverage adequacy for independent re-review; it does not prove absence of exact prior work and does not authorize `first`, `unique`, or `unprecedented` wording.

A fresh pre-submission search remains mandatory.