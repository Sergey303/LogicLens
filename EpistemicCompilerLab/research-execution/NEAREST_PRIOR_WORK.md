# Nearest Prior Work — WP-003

Status: **producer comparison artifact; pending independent review**  
As of: **2026-08-06**

## Common comparison dimensions

The nearest papers are compared on the same dimensions:

1. whether model weights change;
2. whether an LM produces a symbolic representation;
3. whether a trusted runtime executes it;
4. what object is returned after execution;
5. whether an LM remains responsible for final interpretation/rendering;
6. whether `supported`, `refuted`, `unknown`, and `conflicting` are typed and preserved;
7. whether matched raw, teacher-edited, structured-only, executed, and answer-copying controls exist;
8. whether oracle/scorer independence and layer error localization are central.

## LINC — RW-003

**Shared:** LM semantic parsing, FOL execution by an external theorem prover, and evidence that a comparatively small open model benefits from symbolic execution.

**Occupied claim:** an LM can translate natural language into FOL and benefit from an external theorem prover.

**Remaining distinction:** the flagship studies interface placement under one frozen fixed-weight small-model design. Raw context/program, teacher-edited representations, structured controls, executed results, and a typed decision frame are compared; the formal result is consumed by a separate renderer and strict epistemic contract preservation is scored.

## Logic-LM — RW-002

**Shared:** semantic parsing before deterministic inference, solver-driven error feedback, and separation of symbolic inference from free-form LM reasoning.

**Occupied claim:** deterministic symbolic solvers can improve logical reasoning and help refine faulty formalizations.

**Remaining distinction:** the flagship directly contrasts contextual teaching with trusted execution while weights remain fixed. It separates assertion, interpretation, status, policy, frame, and rendering and requires an independent oracle/scorer.

## Faithful Chain-of-Thought — RW-004

**Shared:** translation, symbolic reasoning, and answer construction are separated; deterministic solvers target faithful reasoning.

**Occupied claim:** a translation-plus-solver pipeline can be more faithful than free-form chain of thought.

**Remaining distinction:** the flagship freezes exact epistemic states, policy, provenance, warnings and proof/evidence obligations and uses M6 versus the strongest matched non-compiled baseline—not free-form CoT versus solver alone.

## SatLM — RW-005

**Shared:** LM-generated declarative specification, automated theorem proving, and correctness explicitly conditional on the parsed specification.

**Occupied claim:** declarative specifications plus theorem proving can outperform imperative program-aided reasoning and avoid solver-side planning errors.

**Remaining distinction:** the flagship asks whether a verified **result interface** preserves epistemic behavior better than matched raw or teacher-edited representations, with controls for solver access, structure, tokens, and authoritative answer fields.

## Program-Aided Language Models — RW-001

**Shared:** LM-generated executable representation and deterministic external computation.

**Occupied claim:** executing LM-generated programs can improve reasoning.

**Remaining distinction:** PAL primarily uses execution for program-suitable answers. The flagship focuses on open-world epistemic decisions, keeps a fixed LM as interpreter/renderer after execution, and studies a typed verified decision frame rather than generic program execution.

## Verdict

No nearest paper permits a claim that external symbolic execution, program-aided reasoning, declarative solving, or constrained structured generation is new.

The defensible positive comparison is:

> The study evaluates where formal semantics should be placed in a fixed-weight small-model pipeline by comparing matched contextual, teacher-edited, structured, and trusted-executed interfaces, with a typed strict-epistemic decision contract and independent layer evaluation.

This is a behavioral causal-study boundary, not an invention claim for neuro-symbolic reasoning, Prolog tool use, formal grammars, or knowledge compilation.

## Mandatory adversarial checks

- Show M6 is not merely a ready-answer condition.
- Include the strongest structured/no-authoritative-conclusion baseline.
- Match tokens and output schema.
- Keep non-trivial obligations for the final renderer.
- Separate parser/source errors from solver correctness.
- Refresh forward citations before submission.
