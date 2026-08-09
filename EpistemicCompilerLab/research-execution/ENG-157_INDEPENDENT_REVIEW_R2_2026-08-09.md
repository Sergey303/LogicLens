# ENG-157 / WP-005 — Independent Mutation and Dependency Review R2

Date: 2026-08-09

Reviewer role: **Mutation and Dependency Auditor / Independent Semantic Oracle Adjudicator**.

Reviewer context: `ChatGPT ENG-157 independent re-review R2 / 2026-08-09`.

This is a distinct recorded reviewer context from the 2026-08-09 remediation producer. It is not represented as an independent human or organizational review.

## Decision

**REVISE — no PIVOT.**

The remediation is scientifically much stronger than the 2026-08-06 candidate. The implementation-independent semantic registry, explicit four-state/open-world semantics, policy table, track separation, blind gold adjudication design, clean-room physical boundary, mutation/invariant coverage and human/audit-tool protocols should be retained.

The remaining blockers are narrow but critical: the resolved final candidate contains mutually inconsistent gold/packet/freeze contracts, and the claimed final gold-governance preflight cannot have succeeded against those exact candidate bytes.

## Candidate resolution

Latest non-superseded handoff:

`EpistemicCompilerLab/research-execution/handoffs/WP-005-ENG-157-FINAL-REFREEZE-2026-08-09.json`

Handoff commit:

`914cf7d78788c709ada05a21b46e443b452b2559`

The handoff freezes its candidate as the first parent of the handoff-introducing commit. Git comparison confirms:

`9eeb1d03368f3833f20e8c0048b05594ca7a8fd7 -> 914cf7d78788c709ada05a21b46e443b452b2559`

is exactly one commit and adds only the final handoff.

Therefore the reviewed scientific candidate is:

`9eeb1d03368f3833f20e8c0048b05594ca7a8fd7`

No HOLDOUT or REPLICATION content was accessed.

---

## Accepted remediation elements

The following earlier blockers are substantively addressed and should not be reopened without new evidence:

1. **Gold is no longer an allowed B-oracle input.** `ORACLE_PACKET_CONTRACT` explicitly forbids expected status/action/conclusion/frame/model outputs to B computation.
2. **Semantics are materially more implementable.** `SEMANTIC_REGISTRY.json` freezes canonical JSON, identifiers, typed arguments, scope/version/time, least finite fixpoint, open-world absence, polarity-specific evidence semantics, proof normal form, query outcomes and exact alternatives.
3. **Policy is explicit and declarative.** `POLICY_TABLE.json` has an exact mapping for supported/refuted/conflicting/unknown and query error outcomes.
4. **Gold-query execution, natural-question query scoring, production E2E and renderer ceiling are separately scoped.**
5. **Post-model alternative/gold expansion is prohibited.** Newly discovered ambiguity requires a new benchmark version.
6. **Conformance coverage is explicit.** 18 invariants have positive/negative vectors and mutation/scorer mappings; publication score-field coverage is declared.
7. **Human-audit and audit-tool trust designs are now quantitative/fail-closed protocols.** Their future execution remains downstream evidence, which is appropriate for this design WP.
8. **Clean-room physical enforcement is not reduced to package naming.** The boundary requires an allowlisted mount, no production mount/network/cache inheritance, dynamic access tracing and canaries.

These are real improvements.

---

# Blocking findings

## B1 — CRITICAL — The final candidate's `ORACLE_PACKET_CONTRACT.json` is incompatible with the final gold protocol and with its own claimed validator PASS

At candidate `9eeb1d...`, `GOLD_ADJUDICATION_PROTOCOL.json` freezes polarity-specific outcome fields:

- `expected_positive_evidence_roots`;
- `expected_negative_evidence_roots`;
- `expected_proof_normal_form`;
- plus exact status/action/conclusion/warnings/provenance/policy/version.

The same candidate's `ORACLE_PACKET_CONTRACT.json` still uses the earlier generic fields:

- `expected_evidence_roots`;
- and in the B-oracle forbidden list `expected_proof_trace` rather than the final gold field vocabulary.

It also does not contain the `gold_adjudication_protocol` binding required by the final `validate_oracle_gold_governance.py`.

This is not cosmetic. A conflicting case needs separate positive and negative evidence-root expectations. A generic `expected_evidence_roots` field does not encode the frozen polarity-specific gold contract unambiguously.

More importantly, the exact candidate's final validator source explicitly requires:

- `packet["gold_adjudication_protocol"] == "GOLD_ADJUDICATION_PROTOCOL.json"`;
- the packet B-oracle forbidden set to include `expected_positive_evidence_roots`, `expected_negative_evidence_roots`, and `expected_proof_normal_form`;
- the outcome-gold packet fields to contain the full final gold-protocol output field set.

Those requirements are not satisfied by the candidate packet bytes.

Yet `ENG-157_PRODUCER_PREFLIGHT_FINAL_REFREEZE_2026-08-09.json` records that this validator exited `0` with `PASS` against “fresh exact main bytes”. The evidence and candidate bytes are therefore inconsistent.

### Required remediation

Update the packet contract to the final gold vocabulary and bind the gold-adjudication protocol explicitly. At minimum:

- separate positive/negative evidence roots everywhere they are semantically distinct;
- use one exact proof-field name/normal form across registry, gold, packet and scorer;
- add the protocol/version/hash binding that the validator expects;
- add a cross-artifact schema check so stale generic fields cannot coexist with the final gold contract.

Then execute the validator on the exact frozen candidate and retain machine-readable stdout/result/hash evidence produced from those bytes. Do not merely write a later JSON file saying the previous execution passed.

---

## B2 — CRITICAL — There are three contradictory freeze orders for gold, B-oracle and scorer

The final handoff and `ACCEPTANCE.v1.3.yaml` define the intended authoritative order as:

1. semantic/spec/policy/source-rule freeze;
2. blind query adjudication + query-registry freeze;
3. blind outcome adjudication + outcome-gold freeze;
4. isolated B-oracle computes with gold physically unavailable;
5. B output freezes;
6. B-vs-gold consistency check;
7. scorer freezes;
8. first scored model output may exist.

This is a coherent order and should be kept.

But two normative artifacts disagree:

### `GOLD_ADJUDICATION_PROTOCOL.json`

Its `freeze_order` ends with:

- outcome gold registry frozen;
- scorer source/hash frozen;
- first scored model output.

It does not place B-oracle computation/output/consistency anywhere in the sequence.

### `INDEPENDENCE_BOUNDARY.md`

Section 3 instead says:

1. source/query/spec/policy freeze;
2. **B-oracle computes**;
3. B output freezes;
4. **query-adjudication and outcome-gold hashes freeze**;
5. scorer freezes.

That is the opposite order between B computation and gold freeze from the final acceptance/handoff.

An independent implementation cannot know which lifecycle is normative. This is exactly the circularity/governance boundary WP-005 exists to make unambiguous.

### Required remediation

Choose the `ACCEPTANCE.v1.3` / final-handoff order as the single authority unless there is a strong reason to redesign it, and synchronize:

- `GOLD_ADJUDICATION_PROTOCOL.json`;
- `INDEPENDENCE_BOUNDARY.md`;
- `ORACLE_PACKET_CONTRACT.json`;
- final preflight evidence;
- handoff.

The dedicated governance validator must parse/check the authoritative acceptance freeze order against the other normative artifacts rather than validate each artifact only against its own hard-coded local order.

Add a negative mutation that swaps `B_oracle_computes` and `outcome_gold_registry_hash_frozen`; it must fail.

---

## B3 — HIGH — Dedicated validators are still locally self-consistent rather than candidate-wide consistency validators

The semantic validator is now meaningfully stronger than the old generic wrapper, but the final candidate demonstrates a remaining fail-open class:

- `validate_oracle_gold_governance.py` hard-codes one expected gold-protocol order;
- it does not read `ACCEPTANCE.v1.3.yaml` or `INDEPENDENCE_BOUNDARY.md` and compare their lifecycle semantics;
- `validate_oracle_semantics.py` checks packet field presence and prose references but does not detect the conflicting global freeze order;
- `validate_oracle_boundary.py` itself remains the generic WP acceptance wrapper and does not repair this cross-artifact semantic gap.

Thus multiple individually “PASS”-shaped documents can disagree on the central lifecycle while producer preflight still reports PASS.

### Required remediation

Add one fail-closed **cross-artifact WP-005 consistency validator** that binds at least:

- semantic version;
- policy ID/version;
- packet field vocabulary;
- gold protocol field vocabulary;
- scorer expected-value authority;
- exact authoritative freeze order;
- B gold-denial phase;
- track/claim boundaries;
- post-model mutation prohibition.

It should consume `ACCEPTANCE.v1.x.yaml` (or a machine-readable equivalent authoritative contract) rather than duplicating constants independently.

Add negative fixtures for stale packet vocabulary and freeze-order disagreement.

---

# Prior blockers disposition

Relative to the 2026-08-06 independent review:

- **B1 gold/oracle circularity** — conceptually repaired, but not yet accepted because packet/freeze artifacts are inconsistent (new B1/B2).
- **B2 semantic under-specification** — substantially CLOSED by `SEMANTIC_REGISTRY.json` + `POLICY_TABLE.json`.
- **B3 post-model acceptable alternatives loophole** — CLOSED by explicit benchmark re-version requirement.
- **B4 missing invariant/vector/mutation/scorer matrix** — CLOSED at design level.
- **B5 human-audit protocol under-specified** — CLOSED at design level; actual 120-case audit remains future execution evidence.
- **B6 audit-tool trust boundary absent** — CLOSED at design level; actual audit-tool execution remains future evidence.
- **B7 gold-query overclaim** — CLOSED by explicit track separation.
- **B8 no semantic validator** — PARTIALLY CLOSED; dedicated validators exist, but candidate-wide cross-artifact consistency remains B3.

---

# Bounded remediation

Do **not** redesign the semantics or add new oracle features. The next producer pass should be narrowly limited to:

1. align `ORACLE_PACKET_CONTRACT.json` with final gold fields and bind `GOLD_ADJUDICATION_PROTOCOL`;
2. make one authoritative freeze order identical across acceptance, gold protocol, boundary, packet/scorer lifecycle and handoff;
3. add cross-artifact validator + stale-field/freeze-order negative mutations;
4. run fresh exact-candidate preflight and retain truthful machine-readable evidence;
5. publish a new final handoff as the last commit and return to a distinct reviewer.

No Path B implementation, human audit execution, dependency/canary execution, HOLDOUT or REPLICATION access is required to close these **design-package** blockers. Those execution gates remain downstream and must not be misrepresented as already passed.

## Final verdict

**REVISE.**

The underlying oracle/scorer design is viable and now close to acceptance. No PIVOT is warranted. But the current final candidate cannot be accepted while its packet schema, freeze lifecycle and claimed validator execution contradict one another.
