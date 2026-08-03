# Epistemic DSL v0

Status: **proposed architecture baseline**  
Target runtime: **SWI-Prolog**  
Primary consumer: **LogicLens Epistemic Compiler**  
Primary weak-model boundary: **typed request and verified decision frames**

## 1. Purpose

Epistemic DSL v0 defines a strict, source-grounded language for representing and compiling:

- explicit positive and negative assertions;
- measurements and their uncertainty;
- classifier or expert assessments;
- Subjective Logic opinions;
- posterior probability distributions;
- credible intervals;
- credal bounds over admissible models;
- fuzzy membership functions;
- conflicts and evidence dependencies;
- derived logical conclusions;
- decision policies;
- verified frames for weak language models.

The language extends the current strict epistemic separation already used by LogicLens:

1. source assertions;
2. interpretation of the user request;
3. epistemic conclusion;
4. decision policy;
5. natural-language rendering.

Probability and fuzzy membership must not weaken this separation.

## 2. Core principles

1. **No untyped number exists in the uncertainty model.**
2. **No evidence exists without provenance.**
3. **No evidence is assumed independent without an explicit dependency model.**
4. **Absence of support is not opposition.**
5. **Unknown is not false.**
6. **Conflict is not ignorance.**
7. **A classifier score is not automatically a probability of truth.**
8. **A fuzzy membership value is not a probability of truth.**
9. **A decision is not a world fact.**
10. **Weak models do not perform epistemic arithmetic.**
11. **The runtime result preserves the evidence DAG and assumptions.**
12. **The source language compiles to ordinary validated SWI-Prolog and deterministic numerical kernels.**

## 3. Representation layers

### 3.1. Authoring DSL

The authoring syntax is valid SWI-Prolog syntax based on named dict terms:

```prolog
assertion{
    id: a_dr25_001,
    target: claim(is_planet(koi_7016_01)),
    stance: support,
    provenance: source_ref{
        source: kepler_dr25,
        row: "K007016.01",
        field: "koi_disposition"
    },
    dependency: group(dr25_catalogue_koi_7016_01),
    scope: timeless
}.
```

Named fields are preferred over positional syntax because they:

- make the meaning of every value explicit;
- are easier for a language model to produce safely;
- allow field-order independence;
- support precise compiler diagnostics;
- remain valid SWI-Prolog terms;
- can be transformed through `term_expansion/2`.

### 3.2. Canonical Core IR

The compiler normalizes authoring terms into positional internal terms:

```prolog
ep_assertion(
    a_dr25_001,
    claim(is_planet(koi_7016_01)),
    support,
    source_ref(kepler_dr25, "K007016.01", "koi_disposition"),
    group(dr25_catalogue_koi_7016_01),
    timeless
).
```

Core IR is:

- canonically serialized;
- hashed;
- validated;
- executed;
- included in an epoch package;
- never produced directly by the weak student model.

### 3.3. Verified Decision Frame

The weak renderer receives a closed JSON result rather than source Prolog:

```json
{
  "status": "supported",
  "claim": "is_planet(koi_7016_01)",
  "probability": {
    "expected": 0.87,
    "credible90": {
      "lower": 0.74,
      "upper": 0.95
    },
    "credal": {
      "lower": 0.63,
      "upper": 0.96
    }
  },
  "memberships": {
    "earth_sized": {
      "expected": 0.81,
      "lower": 0.73,
      "upper": 0.88
    }
  },
  "conflict": "low",
  "evidence": ["ev_1", "ev_2"],
  "allowedConclusion": "likely_true",
  "warnings": []
}
```

The weak model explains the frame. It does not recompute it.

## 4. Typed predicate spaces

Each predicate belongs to one declared value space.

```prolog
predicate{
    id: is_planet,
    signature: is_planet(entity(koi)),
    value_space: boolean_claim,
    world: open,
    negation: explicit_evidence
}.

predicate{
    id: radius_earth,
    signature: radius_earth(entity(koi)),
    value_space: measurement(unit(earth_radius)),
    world: open
}.

predicate{
    id: earth_sized,
    signature: earth_sized(entity(koi)),
    value_space: fuzzy_membership,
    range: unit_interval
}.

predicate{
    id: followup_priority,
    signature: followup_priority(entity(koi)),
    value_space: decision,
    range: ordinal([low, medium, high])
}.
```

The value spaces answer different questions:

| Value space | Meaning |
|---|---|
| `boolean_claim` | Whether a proposition is supported, refuted, unknown or conflicting |
| `measurement` | The value or distribution of a quantity |
| `fuzzy_membership` | Degree of correspondence to a vague concept |
| `decision` | What action a policy recommends |

## 5. Closed top-level vocabulary

Epistemic DSL v0 supports only these top-level declarations:

```text
model
predicate
source
source_quality
observation
assertion
assessment
evidence_rule
opinion_model
fuzzy_rule
logical_rule
decision_rule
profile
test
```

Unknown top-level terms are rejected.

## 6. Model declaration

```prolog
model{
    id: kepler_epistemic_v0,
    language: epistemic_dsl_v0,
    default_world: open,
    undeclared_dependency: reject,
    untyped_number: reject,
    missing_provenance: reject,
    unknown_operator: reject
}.
```

Required safe defaults:

- `default_world: open`;
- `undeclared_dependency: reject`;
- `untyped_number: reject`;
- `missing_provenance: reject`;
- `unknown_operator: reject`.

## 7. Sources and provenance

### 7.1. Source declaration

```prolog
source{
    id: kepler_dr25,
    kind: scientific_catalogue,
    title: "Kepler DR25 KOI",
    version: "DR25",
    retrieved_at: "2026-08-03T00:00:00Z",
    content_hash: "sha256:..."
}.
```

### 7.2. Source quality

A source does not receive one universal trust score.

```prolog
source_quality{
    source: kepler_dr25,
    dimensions: [
        coverage: bounded{lower:0.90, upper:0.98, closure:closed},
        extraction_stability: bounded{lower:0.99, upper:1.00, closure:closed},
        temporal_relevance: bounded{lower:0.85, upper:1.00, closure:closed}
    ],
    model: source_quality_kepler_v1
}.
```

Source quality is not automatically multiplied by the probability of a claim.

## 8. Observations

An observation records a measured or registered value. It does not directly assert a hypothesis.

```prolog
observation{
    id: obs_radius_7016,
    target: measure(radius_earth(koi_7016_01)),
    value: normal{
        mean: 1.55,
        standard_deviation: 0.18,
        unit: earth_radius
    },
    provenance: source_ref{
        source: kepler_dr25,
        row: "K007016.01",
        field: "koi_prad"
    },
    dependency: group(stellar_fit_dr25_koi_7016_01),
    observed_at: "2018-01-01"
}.
```

### 8.1. Allowed numerical forms

```prolog
point{
    value: 1.55,
    unit: earth_radius
}.

bounded{
    lower: 1.37,
    upper: 1.73,
    closure: closed,
    unit: earth_radius
}.

normal{
    mean: 1.55,
    standard_deviation: 0.18,
    unit: earth_radius
}.

beta{
    alpha: 47.0,
    beta: 3.0
}.

samples{
    artifact: "sha256:...",
    count: 10000
}.
```

A bare value such as `value: 0.8` is invalid.

## 9. Explicit source assertions

```prolog
assertion{
    id: assert_certified_fp_7016,
    target: claim(is_planet(koi_7016_01)),
    stance: oppose,
    provenance: source_ref{
        source: certified_false_positives_v1,
        row: "K007016.01",
        section: "certified disposition"
    },
    dependency: group(certified_fp_review_7016),
    scope: timeless
}.
```

Allowed stances:

```text
support
oppose
```

`oppose` is explicit negative evidence. It is never inferred from missing support.

## 10. Assessments

A classifier or expert assessment is distinct from a fact probability.

```prolog
assessment{
    id: assess_robovetter_7016,
    target: claim(is_planet(koi_7016_01)),
    value: classifier_score{
        score: 0.91,
        scale: robovetter_disposition_score
    },
    assessor: model(robovetter_dr25),
    calibration: robovetter_dr25_calibration_v1,
    provenance: source_ref{
        source: kepler_dr25,
        row: "K007016.01",
        field: "koi_score"
    },
    dependency: group(robovetter_dr25_koi_7016_01)
}.
```

A trusted calibration adapter is required before an assessment contributes evidence.

## 11. Evidence rules

```prolog
evidence_rule{
    id: robovetter_score_to_evidence_v1,

    input: assessment{
        value: classifier_score{
            score: Score,
            scale: robovetter_disposition_score
        }
    },

    target: claim(is_planet(Target)),

    transform: calibration_table(robovetter_dr25_calibration_v1),

    output: subjective_evidence,

    dependency: preserve_input_group,

    missing_calibration: reject
}.
```

The DSL does not allow an LLM to invent free-form conversion arithmetic in v0.

## 12. Opinion models

```prolog
opinion_model{
    id: is_planet_opinion_v1,

    target: claim(is_planet(Target)),

    evidence: all_applicable,

    fusion: clustered{
        within_dependency_group: averaging,
        across_dependency_groups: cumulative
    },

    prior: beta{
        alpha: 1.0,
        beta: 9.0,
        provenance: prior_model(kepler_candidate_prevalence_v1)
    },

    imprecision: credal_box{
        prior_strength: bounded{
            lower: 1.0,
            upper: 4.0,
            closure: closed
        },
        calibration_error: bounded{
            lower: 0.00,
            upper: 0.05,
            closure: closed
        }
    },

    conflict: preserve,

    output: [
        strict_status,
        subjective_opinion,
        posterior_beta,
        credible_interval_90,
        credal_probability_bounds,
        conflict_index
    ]
}.
```

### 12.1. Subjective opinion

A binary opinion is represented by:

```text
belief
disbelief
uncertainty
base_rate
```

with the invariant:

```text
belief + disbelief + uncertainty = 1
```

Projected probability is a derived value, not an independent field.

### 12.2. Credal extension

The source of truth for imprecision is a set of admissible model parameters, not unrelated intervals over belief, disbelief and uncertainty.

Allowed v0 representation:

```prolog
credal_evidence{
    positive: bounded{lower:40, upper:50, closure:closed},
    negative: bounded{lower:2, upper:6, closure:closed},
    base_rate: bounded{lower:0.35, upper:0.55, closure:closed},
    prior_weight: bounded{lower:1, upper:4, closure:closed}
}.
```

The compiler derives lower and upper projected probability over the admissible model family.

### 12.3. Distinct uncertainty products

The following outputs must remain separate:

- `credible_interval`: variation inside one posterior model;
- `credal_bounds`: variation across admissible models or assumptions;
- `conflict_index`: incompatible supporting and opposing evidence;
- `uncertainty`: uncommitted subjective mass;
- `membership_bounds`: uncertainty in fuzzy membership.

The public contract must not use the unqualified word `interval`.

## 13. Fuzzy rules

```prolog
fuzzy_rule{
    id: earth_sized_v1,

    head: fuzzy(earth_sized(Target)),

    input: measure(radius_earth(Target)),

    membership: trapezoid{
        zero_left: 0.50,
        one_left: 0.80,
        one_right: 1.20,
        zero_right: 1.80,
        unit: earth_radius
    },

    propagation: distribution_expectation_and_bounds,

    output: [
        expected_membership,
        membership_bounds_90
    ]
}.
```

A second example:

```prolog
fuzzy_rule{
    id: temperate_v1,

    head: fuzzy(temperate(Target)),

    input: measure(insolation_earth(Target)),

    membership: trapezoid{
        zero_left: 0.20,
        one_left: 0.50,
        one_right: 1.50,
        zero_right: 2.50,
        unit: earth_insolation
    },

    propagation: distribution_expectation_and_bounds
}.
```

Allowed v0 membership functions:

```text
triangle
trapezoid
piecewise_linear
```

Membership functions are versioned model artifacts. Weak models may select them from an allowlist but may not invent them.

## 14. Strict logical rules

```prolog
logical_rule{
    id: candidate_has_stellar_context_v1,

    head: claim(has_stellar_context(Target)),

    body: all([
        exists(measure(stellar_radius(Target))),
        exists(measure(stellar_temperature(Target)))
    ]),

    semantics: strict,

    missing: unknown
}.
```

A strict logical rule must not contain a field such as `rule_confidence: 0.8`.

If rule applicability is uncertain, this uncertainty must be represented through an evidence rule or an explicitly declared conditional model.

## 15. Decision rules

```prolog
decision_rule{
    id: followup_priority_v1,

    head: decision(followup_priority(Target)),

    inputs: [
        probability{
            target: claim(is_planet(Target)),
            model: is_planet_opinion_v1
        },
        fuzzy{
            target: earth_sized(Target),
            model: earth_sized_v1
        },
        fuzzy{
            target: temperate(Target),
            model: temperate_v1
        }
    ],

    policy: thresholds{
        high: all([
            credal_lower_at_least(0.70),
            earth_sized_expected_at_least(0.60),
            temperate_expected_at_least(0.50)
        ]),
        medium: all([
            credal_upper_at_least(0.60),
            conflict_below(0.40)
        ]),
        otherwise: low
    },

    missing: abstain,

    explanation: required
}.
```

A decision is a policy result, not a base fact.

## 16. Profiles

A profile combines heterogeneous derived values without pretending they share one truth scale.

```prolog
profile{
    id: planet_candidate_profile_v1,

    subject: entity(koi),

    fields: [
        truth{
            target: claim(is_planet(Self)),
            model: is_planet_opinion_v1
        },
        measurement{
            target: measure(radius_earth(Self))
        },
        membership{
            target: fuzzy(earth_sized(Self)),
            model: earth_sized_v1
        },
        membership{
            target: fuzzy(temperate(Self)),
            model: temperate_v1
        },
        decision{
            target: decision(followup_priority(Self)),
            model: followup_priority_v1
        }
    ]
}.
```

## 17. Epistemic result contract

```prolog
epistemic_value{
    target: claim(is_planet(koi_7016_01)),

    strict: strict{
        status: conflicting,
        positive_evidence: [ev_1, ev_2],
        negative_evidence: [ev_3]
    },

    opinion: subjective{
        belief: 0.61,
        disbelief: 0.14,
        uncertainty: 0.25,
        base_rate: 0.10
    },

    posterior: beta{
        alpha: 13.2,
        beta: 3.8
    },

    credible: credible_interval{
        level: 0.90,
        lower: 0.57,
        upper: 0.91
    },

    credal: credal_bounds{
        lower: 0.48,
        upper: 0.94
    },

    conflict: conflict{
        value: 0.31,
        level: moderate
    },

    derivation: derivation{
        model: is_planet_opinion_v1,
        evidence: [ev_1, ev_2, ev_3],
        assumptions: [
            dependency_groups_complete,
            calibration_robovetter_dr25_v1
        ]
    }
}.
```

## 18. Evidence DAG and numerical execution

The runtime must not greedily combine every proof answer as if it were independent evidence.

Safe execution order:

1. SWI-Prolog identifies applicable assertions, observations, assessments and rules.
2. It constructs a proof and evidence DAG.
3. Evidence IDs are canonicalized.
4. Duplicate origins are removed.
5. Dependency groups are validated.
6. The numerical kernel performs fusion once over the normalized DAG.
7. The result is associated with the DAG hash and model hash.

SWI-Prolog tabling is useful for reachability and proof collection. Generic answer subsumption must not be used for non-idempotent Subjective Logic fusion without a proven lattice semantics.

## 19. Compiler pipeline

```text
Authoring DSL
    -> parser / SWI term reader
    -> schema validation
    -> epistemic type checking
    -> provenance validation
    -> dependency analysis
    -> rule and operator allowlist validation
    -> canonical Core IR
    -> Prolog generation
    -> evidence DAG execution
    -> numerical kernel
    -> verified result
    -> decision frame
```

The compiler must reject the candidate before execution when any required semantic field is absent or ambiguous.

## 20. Numerical kernels

### 20.1. SWI-Prolog responsibilities

- graph traversal;
- strict logical derivation;
- evidence selection;
- source and dependency grouping;
- simple interval operations;
- deterministic fuzzy functions;
- provenance and explanation construction.

### 20.2. External deterministic kernel responsibilities

- Beta and Dirichlet quantiles;
- credal optimization;
- sampling;
- sensitivity analysis;
- posterior-sample processing;
- expensive numerical models.

The first implementation may use a bounded JSON protocol between SWI-Prolog and a .NET numerical worker.

## 21. Expected problem classes

### 21.1. Semantic overloading of numbers

A value such as `0.8` may be mistaken for:

- source trust;
- probability of truth;
- fuzzy membership;
- classifier score;
- confidence in extraction;
- rule applicability.

Compiler response: reject bare uncertainty numbers.

### 21.2. Source quality substituted for fact probability

A reliable source may report an uncertain result.

Compiler response: keep source quality, evidence contribution and claim probability in separate types.

### 21.3. Double counting dependent evidence

Several catalogues may reuse one observation.

Compiler response: require dependency groups and reject undeclared independence.

### 21.4. Conflict collapsed into ignorance

Strong support and strong opposition are not the same as little evidence.

Compiler response: preserve strict conflict and a separate conflict index.

### 21.5. Unknown converted to false

Compiler response: open-world semantics by default and explicit negative assertions only.

### 21.6. Invented membership functions

A model may create a fuzzy function that produces a desired result.

Compiler response: membership definitions must be versioned, tested and selected from an allowlist.

### 21.7. Interval explosion

Long interval calculations may expand toward `[0,1]`.

Compiler response:

- retain dependencies;
- provide sensitivity reports;
- distinguish fast conservative bounds from reference bounds;
- report `bounds_unavailable` instead of inventing precision.

### 21.8. Credal inference complexity

Compiler response for v0:

- support only `credal_box`;
- allow at most six free interval parameters per query;
- use vertex evaluation or bounded sampling;
- expose timeout and incompleteness diagnostics.

### 21.9. Decision treated as fact

Compiler response: separate `decision_rule` and `decision` value spaces from `claim`.

### 21.10. Weak model recomputes values

Runtime response: provide a closed decision frame and prohibit arithmetic in the renderer contract.

### 21.11. Invented evidence IDs

Runtime response: evidence IDs are schema-enumerated and unknown IDs invalidate the response.

### 21.12. Temporal validity mixed with confidence

A claim may be well supported but no longer current.

Compiler response: maintain `valid_time`, `observed_at`, `superseded_by` and temporal applicability separately.

## 22. Weak-model roles

A weak model may operate only in these roles:

| Role | Allowed | Forbidden |
|---|---|---|
| Interpreter | Extract explicit values and select an allowed query kind | Compute probability or fuzzy values |
| Tail router | Request evidence, conflict or assumption details | Modify rules or models |
| Renderer | Explain a verified decision frame | Change statuses, values or intervals |
| Proposal assistant | Fill a restricted source-grounded template | Invent operators, priors or calibrations |

A weak model must not:

- author opinion models;
- select a fusion algebra outside an allowlist;
- calculate credible or credal bounds;
- infer source independence;
- create fuzzy membership functions;
- create calibrations;
- strengthen an allowed conclusion.

## 23. Weak interpreter prompt

```text
You are the LogicLens request interpreter. Convert the user request into one structured query. Do not answer the domain question and do not calculate truth, probability, fuzzy membership or a decision.

Allowed query kinds:
- claim
- measurement
- membership
- profile
- explain

Rules:
1. Use only entities and values explicitly present in the request or trusted context.
2. Do not correct or complete identifiers from memory.
3. Do not treat missing knowledge as negative evidence.
4. Do not calculate or estimate numerical values.
5. Select only a model listed in allowedModels.
6. Return need_clarification when a required value is missing.
7. Return ambiguities instead of choosing an unsupported interpretation.
8. Output only JSON matching the response schema.
9. Check that probability was not confused with fuzzy membership.
10. Check that a decision was not confused with a fact about the world.

Output fields:
- action
- queryKind
- target
- model
- explicitValues
- missingFields
- ambiguities
- reason
```

## 24. Weak renderer prompt

```text
You are the renderer of a verified LogicLens Decision Frame. Logical statuses, numerical values, intervals, evidence identifiers and warnings were computed by trusted components. Do not recompute them.

Rules:
1. Preserve strict.status exactly.
2. Never replace unknown with false, no or refuted.
3. Explicitly report conflicting evidence when status is conflicting.
4. Describe probability.expected as the expected probability under the named model.
5. Describe credibleInterval as uncertainty inside one posterior model.
6. Describe credalBounds as variation over admissible models and assumptions.
7. Describe fuzzy membership as degree of correspondence to a concept, not probability.
8. Never merge credible and credal intervals.
9. Follow renderingPrecision exactly.
10. Use only evidence listed in the frame.
11. Do not claim that Prolog proved real-world truth.
12. Preserve warnings and model limitations.
13. Do not use a stronger statement than allowedConclusion.
```

## 25. Restricted weak proposal prompt

```text
You create only an Epistemic DSL v0 proposal. You do not modify the active model and do not create arbitrary functions.

Allowed proposal kinds:
- source
- observation
- assertion
- assessment
- selection of an existing evidence_rule
- selection of an existing fuzzy_rule
- regression test

Forbidden:
- new fusion operators
- invented calibration
- invented source quality
- bare probability or confidence numbers
- assumed independence
- new fuzzy functions without supplied anchor points
- modification of opinion models
- modification of decision policies
- deletion of existing assertions
- unknown source, model or entity IDs

Procedure:
1. Classify the input as observation, explicit assertion, assessment or unknown.
2. Copy only values present in the source.
3. Attach exact provenance.
4. Choose a dependency group from the allowed list or request review.
5. Assign a declared semantic type and unit to every number.
6. Add a positive test.
7. Add the closest counterexample.
8. Return a proposal, never an activation claim.
```

## 26. Teacher error taxonomy

The teacher must locate the earliest faulty layer before changing the system.

Additional error classes:

```text
numeric value lost its type
classifier score treated as probability
probability treated as membership
membership treated as truth
source quality treated as claim probability
dependency group missing
dependent evidence counted twice
explicit opposition confused with absence
credible interval confused with credal bounds
conflict collapsed into uncertainty
decision treated as fact
temporal applicability ignored
unsupported operator selected
calibration used outside its domain
evidence DAG contains duplicate origin
renderer strengthened the verified conclusion
```

Intervention priority:

1. fix value typing;
2. fix query interpretation;
3. fix provenance;
4. fix dependency grouping;
5. fix observation/assertion distinction;
6. fix evidence adapter;
7. fix calibration;
8. fix fuzzy definition;
9. fix opinion model;
10. fix decision policy;
11. only then change prompt or model.

## 27. Epistemic DSL v0.1 implementation scope

### 27.1. Required declarations

```text
model
predicate
source
observation
assertion
assessment
fuzzy_rule
evidence_rule
opinion_model
profile
test
```

### 27.2. Required numerical forms

```text
point
bounded
normal
beta
credal_box
```

### 27.3. Required fuzzy forms

```text
triangle
trapezoid
piecewise_linear
```

### 27.4. Required fusion forms

```text
averaging
cumulative
clustered
```

`clustered` means:

- averaging within one dependency group;
- cumulative fusion across independent groups.

### 27.5. Required outputs

```text
strict status
subjective opinion
Beta posterior
credible interval
credal bounds
conflict
fuzzy membership
evidence DAG
```

### 27.6. Explicit non-goals for v0.1

```text
arbitrary probabilistic rules
Bayesian-network DSL
recursive numerical fusion
user-defined t-norms
unbounded credal constraints
causal inference
automatic membership learning
arbitrary LLM-generated mathematical expressions
```

## 28. Required compiler tests

### 28.1. Positive tests

1. A point measurement with provenance compiles.
2. A normal measurement propagates through a trapezoidal fuzzy function.
3. Explicit support and opposition produce `conflicting`.
4. Missing evidence produces `unknown`.
5. A calibrated assessment contributes typed evidence.
6. Evidence from one dependency group is not cumulatively double-counted.
7. Distinct dependency groups are fused according to the opinion model.
8. Credible and credal outputs are present as separate fields.
9. A decision policy consumes probability and membership without converting itself into a claim.
10. A decision frame preserves evidence and model identifiers.

### 28.2. Negative tests

1. Reject bare `value: 0.8`.
2. Reject an assertion without provenance.
3. Reject a numerical observation without a unit when the predicate requires one.
4. Reject an assessment without calibration.
5. Reject undeclared source independence.
6. Reject a fuzzy rule containing a probability field.
7. Reject an opinion model with unrelated intervals over belief, disbelief and uncertainty.
8. Reject a strict rule with `rule_confidence`.
9. Reject an unknown fusion operator.
10. Reject evidence IDs not present in the compiled DAG.
11. Reject a decision rule used as a base claim.
12. Reject a weak-model proposal that creates a membership function.
13. Reject a renderer response that changes `unknown` to `refuted`.
14. Reject a renderer response that merges credible and credal intervals.
15. Reject a candidate whose numerical output is not reproducible under the pinned kernel.

## 29. Canonical architectural formula

```text
Raw layer:
    observation
    assertion
    assessment
    provenance
    dependency

Semantic layer:
    strict claim
    measurement
    fuzzy membership
    opinion model
    decision

Compilation layer:
    typed validation
    evidence mapping
    DAG construction
    dependency analysis
    numerical inference

Output layer:
    strict status
    subjective opinion
    posterior
    credible interval
    credal bounds
    conflict
    fuzzy values
    evidence DAG
```

## 30. Final invariant

> No number exists without the name of its meaning.  
> No evidence exists without provenance and dependency.  
> No decision is called a fact.  
> A weak model does not calculate the epistemic result: it selects a query, requests the necessary evidence and explains a verified frame.
