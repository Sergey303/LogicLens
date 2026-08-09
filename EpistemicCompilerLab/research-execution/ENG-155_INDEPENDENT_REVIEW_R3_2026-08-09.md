# ENG-155 / WP-003 — Independent Related-Work Review R3

Date: 2026-08-09

Reviewer role: **Research Program Architect**.

Reviewer context: `ChatGPT ENG-155 independent related-work re-review R3 / 2026-08-09`.

This is a distinct reviewer context from the Q13/Q14 remediation producer. It is not represented as independent human or organizational review.

## Decision

**REVISE — freshness/saturation only. No PIVOT.**

The Q13/Q14 remediation correctly removes novelty claims for decision graphs/SOP routing, Prolog routing, tool-schema adaptation, executable Python, teacher-generated SFT/LoRA/distillation and weight-changing Qwen transfer. The surviving flagship claim remains appropriately narrow:

> preregistered matched causal evaluation of authoritative semantic-result placement for fixed-weight small language models under a four-state strict epistemic contract, with shortcut controls and an independently implemented layer-specific oracle/scorer.

I found no primary work in this re-review that establishes the full combined causal profile above. Therefore the central novelty boundary does **not** require PIVOT on the present evidence.

However, the producer's statement that Q13/Q14 are the latest usable saturation evidence cannot be accepted. A fresh primary-source attack on 2026-08-09 surfaced several materially relevant July/August 2026 works absent from the repository matrix and screening ledger.

## Candidate reviewed

Producer handoff commit:

`497896d74b5607b5d4bb853e2a5a2be0e0e5ccb0`

The candidate reports 58 primary sources, 14 structured comparisons, eight mandatory transfer-ladder controls, and Q13/Q14 as the latest usable saturation rounds.

No HOLDOUT or REPLICATION content was accessed.

## Previous round-2 blocker disposition

The round-2 requested transfer-ladder refresh itself is substantively complete:

- SOP/decision-graph routing is treated as occupied mechanism territory;
- tool-schema naming is treated as a causal alternative explanation;
- teacher-generated weight adaptation/distillation is treated as established and separate from the fixed-weight core;
- ENG-200/201/202 are boundary/falsification comparators rather than novelty claims;
- Q13/Q14 candidate-level ledgers and semantic validation exist.

Those changes should be retained.

## New blocking finding — HIGH — Q13/Q14 saturation is not fresh enough to support final W0 coverage

The repository's Q13 search round is explicitly the final usable router/schema attack and reports only six inspected unique primary candidates. Fresh independent search found multiple primary works published before or around that refresh that are absent from `RELATED_WORK_MATRIX.csv`, the screening ledger and the seven-dimension ledger.

### 1. ToolGate: Contract-Grounded and Verified Tool Execution for LLMs

ACL Findings 2026, Anthology `2026.findings-acl.470`.

Material overlap:

- explicit typed symbolic trusted state;
- tool preconditions/postconditions expressed as formal contracts;
- deterministic runtime verification before results are committed;
- explicit goal of logical safety/verifiability for LLM tool execution.

This occupies additional broad territory around **typed trusted state + contract-grounded verified execution**. It is not an exact match to the flagship because the paper does not, from the primary source inspected here, establish the full fixed-weight-small-model/four-state/matched-authoritative-result-placement/independent-layer-oracle design.

Nevertheless it is sufficiently close that it must be included or explicitly screened with seven-dimension disposition before saturation can be claimed.

Primary source: ACL Anthology, https://aclanthology.org/2026.findings-acl.470/

### 2. Text2Mem: A Unified Memory Operation Language for Memory Operating System

ACL Findings 2026, Anthology `2026.findings-acl.100`.

Material overlap:

- schema-based contracts with explicit semantic invariants;
- validated schemas parsed into typed operation objects;
- deterministic execution pipeline;
- SQL reference backend plus real backends;
- benchmark explicitly decouples schema generation from backend execution to evaluate planning vs execution fidelity.

This further occupies **typed executable contract / SQL reference backend / generation-vs-execution decomposition** territory and is directly relevant to ENG-197/199 and to the claim boundary around typed result interfaces.

It does not appear to establish the full flagship causal profile, so no PIVOT is warranted, but it must be dispositioned.

Primary source: ACL Anthology, https://aclanthology.org/2026.findings-acl.100/

### 3. LatentGate: Low-Latency Semantic Routing via Frozen-Backbone Probing of Small Language Models

ACL 2026 Industry Track, Anthology `2026.acl-industry.153`.

Material overlap:

- explicitly frozen small language model backbone;
- routing as the target problem;
- comparison against prompt-based and embedding routing baselines;
- multiple SLM backbones and OOD routing evaluation.

The learned linear probe means this is not the same fixed-weight interface treatment as ENG-200, but it is a mandatory neighboring control/background item for any claim about routing under frozen SLM backbones.

Primary source: ACL Anthology, https://aclanthology.org/2026.acl-industry.153/

### 4. Rethinking Scale: Deployment Trade-offs of Small Language Models under Agent Paradigms

ACL 2026 Industry Track, Anthology `2026.acl-industry.123`.

Material overlap:

- open-source models below 10B;
- direct/base vs tool-equipped single agent vs routing-based multi-agent comparison;
- explicit result that routing coordination overhead may deliver limited gains under small-model constraints.

This is not an exact semantic-placement paper, but it is directly relevant conventional evidence for the project's small-model tool/routing boundary and should be included or explicitly excluded with rationale.

Primary source: ACL Anthology, https://aclanthology.org/2026.acl-industry.123/

### 5. Don't Offer What Can't Be Done: Deterministic Executability Gating for LLM Skill Selection at Scale

arXiv `2608.01050`, submitted 2026-08-02.

Material overlap:

- deterministic executability gate driven by authoritative account state;
- gate removes impossible skills before the LLM chooses among remaining candidates;
- counterfactual replay tests whether deterministic gating changes model selection rather than only context size.

This is especially relevant to ENG-200's executed-router/gating interpretation. As an arXiv preprint it need not be elevated above peer-reviewed ACL controls, but it must at least appear in the screening/disposition ledger because it predates the final Q13/Q14 handoff.

Primary source: arXiv 2608.01050.

### 6. Guidelines as Environments: A World Model Approach to Rule Following

ACL 2026 long paper `2026.acl-long.741`.

The primary abstract describes explicit evolving state for interdependent rules that can trigger, suppress or conflict. It is adjacent to the strict-rule/conflict-state side of the flagship and should be screened for the four-state/rule-execution dimensions rather than silently absent.

Primary source: ACL Anthology, https://aclanthology.org/2026.acl-long.741/

## Why this blocks PASS but not the central claim

The current saturation ledger says Q13/Q14 are the latest usable rounds and that no candidate reaches five strict YES dimensions. But a zero-match saturation statement is only meaningful over the candidate set actually surfaced and dispositioned. ToolGate/Text2Mem/LatentGate/Rethinking Scale were all discoverable primary 2026 work and do not appear anywhere in the repository search/matrix artifacts at the reviewed candidate.

This does **not** demonstrate that any of them reaches the five-of-seven threshold. Based on the primary-source material inspected in this review, none obviously matches all critical dimensions, and no exact prior work was found.

The issue is therefore **coverage freshness**, not novelty collapse.

## Bounded remediation

Do not reopen the entire 58-source review. Add one bounded fresh round, e.g. `Q15`, centered on:

- contract-grounded verified tool execution;
- typed trusted/symbolic state and result-commit verification;
- schema-based executable operation languages and SQL reference backends;
- frozen-backbone SLM routing;
- deterministic executability gates / capability pruning using authoritative state;
- explicit-state rule following under conflicts.

At minimum screen/disposition the six works listed above using the existing seven-dimension machinery. Add materially relevant included papers to the matrix and structured-control tables.

Update `NOVELTY_BOUNDARY.md` explicitly so that broad novelty is also disclaimed for:

- typed symbolic state plus Hoare-style/contract-gated verified tool execution;
- schema-contract languages with typed execution objects and SQL reference backends;
- frozen-backbone SLM routing/probing;
- deterministic executability gating from authoritative state.

The positive surviving claim should remain unchanged unless Q15 actually finds a source matching the full causal profile.

The semantic validator should require the latest usable saturation round to include these mandatory anchors/dispositions and should fail if Q13/Q14 are still labeled final after the Q15 refresh.

## Final verdict

**REVISE.**

No evidence found in this review requires PIVOT of the fixed-weight authoritative-semantic-result-placement core. But WP-003 cannot receive PASS while its final saturation claim omits materially adjacent 2026 primary work that predates the final refresh.
