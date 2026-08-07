# ENG-200 — Teacher-generated routing comparator

Status: **producer candidate, TRAIN/DEV prototype only; independent review required**  
Parent: `WP-004 / ENG-156`  
Scientific label: **teacher-generated routing-policy comparator**

## Objective

Test whether a strong teacher can compile reusable routing knowledge for fixed-weight Qwen without changing Qwen weights and without letting the router perform domain reasoning.

The prototype separates:

- **M19 Executed Teacher Router:** deterministic runtime executes the accepted policy before Qwen;
- **M20 Explained Teacher Router:** Qwen sees the same policy explanation plus a typed capability catalogue and chooses the capability itself;
- **tree vs Prolog representation:** both are lowerings/executors of one canonical routing IR;
- **schema/name adaptation:** a separate DEV-only presentation factor, never bundled silently into the routing-policy treatment.

## Scientific ownership

The router may only select a capability from typed request features. It does not compute epistemic status, action, conclusion, SQL rows, Prolog proofs, Python results, or final natural-language answers.

The eventual upstream feature extractor is independent of the teacher policy. The synthetic prototype therefore starts from typed features to validate routing semantics without conflating natural-language parsing.

## Existing-work boundary

Decision graphs/SOP routing, tool filtering, Prolog/rule routers, and tool-schema adaptation are established techniques. ENG-200 does not claim novelty for those mechanisms. Its purpose is to create matched falsification/control arms for the broader fixed-weight interface-placement study.

## Machine-checkable outputs

- `ROUTING_CAPABILITY_REGISTRY.yaml`
- `ROUTING_MODE_CONTRACTS.yaml`
- `TEACHER_ROUTING_IR.schema.json`
- `TEACHER_POLICY_GENERATION_CONTRACT.md`
- `DECISION_GRAPH_CONTRACT.md`
- `PROLOG_ROUTER_CONTRACT.md`
- `ROUTING_EQUIVALENCE_TESTS.md`
- `FEASIBILITY_INPUT.json`
- `prototype/policy.ir.json`
- `prototype/cases.train_dev.json`
- `prototype/decision_graph.py`
- `prototype/generate_policy.py`
- `prototype/generate_visible_catalogue.py`
- `prototype/generated/policy.pl`
- `prototype/generated/qwen-catalogue.neutral.json`
- `prototype/generated/qwen-catalogue.adapted.json`
- `prototype/policy-explanation.neutral.md`
- `prototype/verify.py`

## Reproduction

From the package directory:

```text
python prototype/generate_policy.py
python prototype/generate_visible_catalogue.py
python prototype/verify.py --require-swipl
```

The final command requires SWI-Prolog and exhaustively compares both routing representations over the complete frozen feature space.

Windows launcher after merge:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' router-comparator-tests
```

## STOP / PIVOT

- If direct Qwen selection matches teacher routing, drop the teacher-router arm.
- If a simple static/human SOP router matches the teacher-generated policy, do not claim teacher-specific value.
- If M19 is strong but M20 weak, routing execution helps but Qwen cannot reliably follow the policy explanation.
- If neutral versus schema-adapted labels materially change routing, report schema alignment separately.
- If tree and Prolog route identically, prefer the simpler representation unless an engineering criterion justifies Prolog.
- No routing mode enters HOLDOUT before WP-004/WP-006/WP-007 adjudication.
