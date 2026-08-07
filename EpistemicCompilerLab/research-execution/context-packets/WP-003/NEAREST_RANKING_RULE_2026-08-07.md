# WP-003 nearest-neighbour ranking rule

Date frozen: 2026-08-07

This rule exists so `nearest` is not assigned by rhetoric, citation count, or whichever paper is convenient for the flagship claim. The output is an **adversarial comparison priority**, not a claim that one scalar perfectly captures scientific similarity.

## 1. Eligibility gate

A source is eligible for the **core nearest-neighbour ranking** only when all of the following hold:

1. it is an included primary source in `RELATED_WORK_MATRIX.csv`;
2. it is not included solely as a control/evaluator/training/terminology family;
3. at least one of these defining dimensions is `yes`:
   - D2 matched interface/representation contrast;
   - D3 trusted deterministic execution of formal/tool semantics;
4. it materially changes where procedure/domain semantics are represented or executed, rather than only measuring a downstream behavioural shortcut.

A source failing this gate may still be a mandatory adversarial control. In particular, RW-050 (Readout Shortcut) is mandatory for the answer-copying control but is not a compiler/runtime nearest neighbour.

## 2. Distance score

For eligible sources, map dimension values to numeric match values:

- `yes = 1.0`
- `partial = 0.5`
- `unclear = 0.0`
- `no = 0.0`

Compute:

```text
score =
  2*D1  fixed-weight small/open student
+ 4*D2  matched interface/representation causal contrast
+ 4*D3  trusted deterministic semantic execution
+ 5*D4  four-state strict epistemic status
+ 3*D5  verified result consumed by an LM renderer
+ 3*D6  structure/no-conclusion and answer-copying controls
+ 2*D7  independent layer-specific oracle/scorer
```

D4 receives the highest weight because it is the most specific surviving flagship boundary. D2 and D3 are next because the work package asks specifically about causal interface placement and trusted execution, not generic small-model behaviour.

## 3. Tie breakers

If scores tie, compare in this order:

1. higher D4;
2. higher D2;
3. higher D3;
4. higher D5;
5. more recent primary-source version date;
6. lexicographically smaller `source_id` for deterministic final ordering.

## 4. Mandatory architecture anchors and final selection

A pure scalar score can hide a qualitatively distinct occupied architecture. The final comparison set is therefore selected deterministically in two stages.

**Stage A — reserve three architecture-anchor slots, in this order:**

1. RW-042 SIGIL — typed AG-IR, prose-vs-harness causal comparison, deterministic lowering, model/code ownership and provenance;
2. RW-038 SkillSmith — offline compiled executable boundary contracts and stronger-model artifact reuse across runtime models;
3. RW-039 Ontology-to-tools — formal ontological semantics compiled into executable LLM tool interfaces.

These are mandatory because the independent review requires the surviving claim to be attacked against all three qualitatively different occupied territories: typed harness compilation, small/efficient-model compiler-runtime reuse, and executable formal-domain semantics.

**Stage B — fill remaining comparison slots** from eligible non-anchor sources in descending distance score using the tie breakers above.

The anchor reservation is an **adversarial inclusion floor**, not a producer assertion that RW-039 has a larger scalar similarity score than every procedural compiler paper. Both the raw score and the anchor rule remain visible so a reviewer can challenge either choice.

Mandatory control sources such as RW-050 are compared in the causal-design/control section even when they are not eligible for the compiler/runtime nearest list.

## 5. Saturation rule

A post-refresh round may contribute to saturation only if:

- every included matrix source has a seven-dimension ledger row;
- every screened exclusion from that round has a screening-ledger row and explicit reason;
- the round records the exact queries and number of unique primary candidates actually opened/screened;
- no newly screened source reaches at least five `yes` values out of seven;
- no source occupies the exact positive causal comparison even if it scores below five due to one unusually specific dimension.

Two consecutive eligible post-refresh rounds are necessary but not sufficient for a producer to report **provisional search saturation**. The independent reviewer still decides whether the search coverage is adequate; saturation never licenses `first`, `unique`, or `unprecedented` wording.
