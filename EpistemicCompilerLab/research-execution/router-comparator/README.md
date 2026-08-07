# ENG-200 — Teacher-generated routing comparator

Status: **remediation producer candidate, TRAIN/DEV prototype only; independent review required**  
Parent: `WP-004 / ENG-156`  
Scientific label: **teacher-generated routing-policy comparator**

## Objective

Test whether a strong teacher can compile reusable routing knowledge for fixed-weight Qwen without changing Qwen weights and without letting the router perform domain reasoning.

The prototype separates:

- **M19 Executed Teacher Router:** deterministic runtime executes the accepted policy from a frozen typed feature vector before Qwen;
- **M20 Explained Teacher Router:** Qwen receives the **same frozen typed feature vector**, the same typed capability catalogue, and the teacher policy explanation, then chooses the capability;
- **direct-Qwen baseline:** Qwen receives the same frozen typed feature vector and catalogue but no teacher policy;
- **raw-question feature extraction:** separate DEV-only ablation, never bundled into the primary M19-vs-M20 contrast;
- **tree vs Prolog representation:** both are executors/lowerings of one canonical routing IR;
- **schema/name adaptation:** a separate DEV-only presentation factor.

## Scientific ownership

ENG-200 selects a **capability only**.

It does not:

- parse raw questions in the primary routing contrast;
- compute epistemic status, action, conclusion, SQL rows, Prolog proofs, Python results, or final answers;
- bind tool arguments.

Feature preparation is governed by `ROUTING_FEATURE_CONTRACT.json`. Argument binding is governed by `ARGUMENT_BINDING_CONTRACT.md` and is held equal across routing arms.

## Typed capability contract

`ROUTING_CAPABILITY_REGISTRY.yaml` references machine-valid input and result schemas in `CAPABILITY_IO_SCHEMAS.json`. Every capability also freezes:

- provenance requirement;
- side-effect contract;
- execution budget;
- failure codes and fail-closed semantics;
- neutral and schema-adapted Qwen-visible surfaces.

Generated Qwen catalogues embed the typed schemas and execution contracts but never expose internal canonical capability IDs.

## Existing-work boundary

Decision graphs/SOP routing, tool filtering, Prolog/rule routers, and tool-schema adaptation are established techniques. ENG-200 does not claim novelty for those mechanisms. Its purpose is to create matched falsification/control arms for the broader fixed-weight interface-placement study.

## Machine-checkable outputs

Core contracts:

- `ROUTING_FEATURE_CONTRACT.json`
- `ROUTING_CAPABILITY_REGISTRY.yaml`
- `ROUTING_CAPABILITY_REGISTRY.schema.json`
- `CAPABILITY_IO_SCHEMAS.json`
- `ROUTING_MODE_CONTRACTS.yaml`
- `ARGUMENT_BINDING_CONTRACT.md`
- `TEACHER_ROUTING_IR.schema.json`
- `TEACHER_POLICY_GENERATION_CONTRACT.md`
- `DECISION_GRAPH_CONTRACT.md`
- `PROLOG_ROUTER_CONTRACT.md`
- `ROUTING_EQUIVALENCE_TESTS.md`
- `RUNTIME_DEPENDENCIES.yaml`
- `ENG-200_FREEZE_MANIFEST.json`

Executable prototype:

- `prototype/policy.ir.json`
- `prototype/cases.train_dev.json`
- `prototype/feature_adapter.py`
- `prototype/decision_graph.py`
- `prototype/generate_policy.py`
- `prototype/generate_visible_catalogue.py`
- `prototype/build_freeze_manifest.py`
- `prototype/generated/policy.pl`
- `prototype/generated/qwen-catalogue.neutral.json`
- `prototype/generated/qwen-catalogue.adapted.json`
- `prototype/policy-explanation.neutral.md`
- `prototype/verify.py`
- `prototype/verify_leakage_mutation.py`

## Reproduction

From the package directory:

```text
python prototype/generate_policy.py
python prototype/generate_visible_catalogue.py
python prototype/build_freeze_manifest.py --check
python prototype/verify_leakage_mutation.py
python prototype/verify.py --require-swipl
```

The final command requires SWI-Prolog and exhaustively compares both routing representations over the complete frozen feature space.

## STOP / PIVOT

- If direct Qwen selection matches teacher routing, drop the teacher-router arm.
- If a simple static/human SOP router matches the teacher-generated policy, do not claim teacher-specific value.
- If M19 is strong but M20 weak, routing execution helps but Qwen cannot reliably follow the policy explanation.
- If neutral versus schema-adapted labels materially change routing, report schema alignment separately.
- If tree and Prolog route identically, prefer the simpler representation unless an engineering criterion justifies Prolog.
- No routing mode enters HOLDOUT before WP-004/WP-006/WP-007 adjudication.
