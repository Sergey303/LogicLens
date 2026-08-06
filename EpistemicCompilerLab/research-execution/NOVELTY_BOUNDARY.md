# Novelty Boundary — Compile, Don't Teach

Status: **NARROW; pending independent review**  
Work package: `WP-003 / ENG-155`  
As of: **2026-08-06**

## Decision

The search does not support `first`, `unique`, `unprecedented`, or a general neuro-symbolic-method claim.

It also does not currently require a full PIVOT or STOP. No single reviewed source matched the complete flagship causal design, but broad components are occupied. Novelty must be stated as a positive comparison, never as proof by absence.

## Occupied territory

### External deterministic execution

PAL, Program of Thoughts, Faithful Chain-of-Thought, SatLM, Logic-LM, LINC, Binder, and NLEP already establish LM-generated programs or symbolic specifications, external execution, and gains from offloading computation or deduction. Correctness is commonly conditional on the parsed specification.

The flagship may not present solver-aided or program-aided reasoning as its invention.

### Tool use and modular systems

MRKL, ReAct, Toolformer, ART, Gorilla, ToolLLM, and CRITIC occupy routing, tool calls, observations, and modular neural/discrete systems.

Keeping a model fixed while calling an external tool is not by itself a contribution.

### Structured generation

PICARD, grammar-constrained decoding, LMQL, guided generation, SynCode, XGrammar, JSONSchemaBench, and grammar-constrained logical parsing occupy syntactic and schema guarantees.

Typed JSON alone is not the contribution. The primary result must survive a structured-output control without an authoritative computed conclusion.

### Prompt and program optimization

APE, OPRO, ProTeGi, DSPy, Promptbreeder, EvoPrompt, Self-Refine, and CRITIC occupy automatic prompt generation, textual feedback, optimization of prompts/demonstrations, and refinement.

The flagship may study bounded effects and failures of contextual teaching, but may not imply prompt/program optimization is new or universally ineffective.

### Training and verifier-guided reasoning

Weak-to-Strong Generalization, process supervision, FRODO, and Prolog-tool training occupy weight-changing teacher/student supervision, learned verifiers, and training small models to use formal tools.

The flagship's distinction is immutable weights and interface placement—not superiority to all trained systems.

## Positive remaining contribution

Subject to later W0 gates, the allowed contribution is:

> A preregistered behavioral study of interface placement for fixed-weight small language models, comparing matched raw, teacher-edited, structured, and trusted-executed representations, where formal semantics are returned through a typed strict-epistemic decision frame and evaluated with an independent layer-specific oracle/scorer.

It has five inseparable parts:

1. **Causal comparison:** M6 versus the strongest matched non-compiled baseline, not M6 versus Raw Prolog alone.
2. **Fixed-weight boundary:** identical frozen student artifacts across conditions.
3. **Strict epistemic contract:** distinct `supported`, `refuted`, `unknown`, and `conflicting` outcomes with policy, provenance, warnings, and proof/evidence obligations.
4. **Result-interface study:** execution precedes final LM rendering; structured-only and answer-copying controls isolate the mechanism.
5. **Independent layer evaluation:** source, query, runtime status, policy, frame transport, and rendering are scored separately without importing the production compiler.

Removing any part risks collapsing the claim into occupied territory.

## Claim decisions

| Candidate claim | Decision | Allowed replacement |
|---|---|---|
| We introduce neuro-symbolic reasoning for LLMs. | Delete | Prior work already combines LMs and symbolic solvers. |
| We are the first to execute Prolog or formal programs for an LM. | Delete | External execution and Prolog tool use are established. |
| Compiled frames are better than Raw Prolog. | Narrow | Compare M6 with the DEV-selected strongest matched non-compiled baseline and matched controls. |
| Typed JSON improves reliability. | Narrow | Attribute only effects surviving structured-output and token controls. |
| Teacher editing does not work. | Narrow | Report effect, variance, and regressions for the frozen scope. |
| Compilation moves execution into an auditable contract. | Conditional retain | Retain only if matched controls, independent oracle, and layer audit support it. |
| The method generalizes. | Narrow | Name evaluated model, domain, source-family, and replication strata. |
| The architecture is privacy preserving. | Delete | Describe data-flow separation only; privacy is separate future work. |
| Runtime correctness proves source truth. | Delete | Correctness is only relative to validated loaded assertions and rules. |
| This is the first such study. | Delete | Use the positive comparison without priority wording. |

## Viability conditions

The central claim survives only if:

- baseline selection is frozen on DEV;
- the scenario-level clustered effect is practically meaningful;
- the direction replicates independently;
- structured/no-conclusion and answer-copying controls do not explain it;
- no one model/domain/status/source family creates the pooled effect;
- independent oracle/scorer and mutation audits pass.

Null or negative evidence forces a boundary or failure-analysis paper.

## PIVOT / STOP

PIVOT before scaling if a refresh finds a paper combining fixed-weight small students, contextual/raw/teacher-edited interfaces, trusted executed results, typed strict states, matched copying/structure controls, and independent layer evaluation.

STOP the flagship route if the only favorable comparison is solver versus no solver, M6 loses to the matched control, the frame is merely the expected answer, evaluator independence fails, replication reverses, or the paper requires universal/privacy/learning/`first` wording.

## Saturation boundary

The recent Prolog/formal-verification refresh and the following citation-chain round added no exact causal-design match, so producer search reached provisional saturation. This is not proof of absence.

Refresh is mandatory before final claim freeze and immediately before submission. Any newly occupied claim must be narrowed or removed.
