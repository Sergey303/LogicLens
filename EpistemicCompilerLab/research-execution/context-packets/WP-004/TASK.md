# WP-004 — Causal design and strongest matched controls

Linear issue: `ENG-156`  
Phase: `W0`  
Kind: `work_package`  
Acceptance gate: `GATE-001`

## Ownership

- Producer: **Causal Experiment Reviewer**
- Independent reviewer: **Senior Adversarial Gatekeeper**
- Gatekeeper: **Senior Adversarial Methodology Reviewer**
- Separate identity, session and conflict declaration are mandatory.

## Why now

The headline deployed-interface effect, competing mechanism explanations, conventional executable alternatives and fixed-weight/weight-changing boundary must be frozen before benchmark construction and final power/feasibility decisions.

## Exact actions

1. Freeze exactly one primary **multi-component deployed-interface bundle estimand**, `M6 vs M14(global B*)`, with `base_scenario_id` as the independent unit. Do not represent the headline as a one-factor mechanism contrast.
2. Define matched secondary falsification contrasts for result-interface serialization, explicit conclusion, minimal status+action decision contract, deterministic rendering, corruption detectability, compiler boundary, token/padding effects and profile-wise strongest baselines.
3. Freeze exact visible/hidden inputs, semantic ownership, failure layers, matching transformations and budgets for active modes.
4. Adjudicate proposed M15–M22 and the ENG-202 weight-changing boundary **conditionally**: producer artifacts do not activate modes. Distinct child review, WP-006 power and WP-007 feasibility are required before any pre-HOLDOUT activation.
5. Fail closed on cross-package identifier drift. WP-002 claims, WP-006 statistics and WP-007 feasibility must bind the exact primary contrast/estimand/baseline/unit/endpoint semantics before WP-004 becomes freeze-ready.

## Deliverables

- `EpistemicCompilerLab/research-execution/CAUSAL_CONTRASTS.yaml`
- `EpistemicCompilerLab/research-execution/MODE_CONTRACTS/`
- `EpistemicCompilerLab/research-execution/ALTERNATIVE_EXPLANATIONS.md`
- `EpistemicCompilerLab/research-execution/BASELINE_SELECTION_RULE.yaml`
- `EpistemicCompilerLab/research-execution/ESTIMANDS.yaml`
- `MODE_CONTRACTS/TRANSFER_LADDER_ADJUDICATION.yaml`
- `MODE_CONTRACTS/WEIGHT_BOUNDARY_ADJUDICATION.yaml`
- `MODE_CONTRACTS/M13_MUTATION_CONTRACT.yaml`
- `MODE_CONTRACTS/M11_RENDERER_COMPARABILITY.yaml`
- `MODE_CONTRACTS/PADDING_INVARIANCE_CONTRACT.yaml`
- `MODE_CONTRACTS/CROSS_PACKAGE_ALIGNMENT.yaml`
- a dedicated non-mutating WP-004 semantic validator and machine-readable validation report;
- immutable producer handoff only after all freeze blockers are actually resolved.

## Producer completion versus freeze readiness

Local semantic consistency and freeze readiness are separate states.

- A producer may reach `LOCAL_SEMANTICS_PASS_FREEZE_BLOCKED` while upstream child reviews, WP-002/WP-006 alignment, WP-007 feasibility, or exact endpoint identity remain unresolved.
- `FREEZE_READY` is forbidden until the dedicated validator finds zero blockers and a distinct independent reviewer accepts the candidate.
- Existence of a child producer handoff cannot be coerced into independent acceptance.

## STOP / PIVOT

- PIVOT to minimal status+action decision-contract if rich-frame effect cannot be separated from ready-answer/minimal-decision availability.
- State LLM rendering is unnecessary if M11 is non-inferior under the frozen renderer criterion.
- Prefer simpler relational/hybrid/general executable interfaces if they match M6 under accepted powered/feasible contrasts.
- Narrow before benchmark construction if no powered and feasible subset preserves the primary estimand and strongest falsification controls.

Do not move this package to `Done` from the producer session. Producer completion means immutable handoff plus `In Review`; the current package must remain `In Progress` while freeze blockers are open.
