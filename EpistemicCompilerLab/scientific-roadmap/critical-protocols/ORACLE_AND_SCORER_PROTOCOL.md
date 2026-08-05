# Oracle and Scorer Protocol
Статус: **MUST freeze before HOLDOUT**
## 1. Independent implementations
Production path:
```text
A = JSON/DSL compiler + SWI-Prolog
```
Validation path:
```text
B = independently implemented oracle/scorer
```
B MUST NOT:
- import production compiler modules;
- call production predicates;
- reuse generated expected frames;
- read student prompts;
- infer gold from model output.
A and B MAY share only frozen schemas and written semantic specification.
## 2. Differential validation
Before freeze execute:
1. A versus B over all non-sealed development cases.
2. Property-based tests over generated valid inputs.
3. Mutation tests for every critical field.
4. Intentionally invalid frames and provenance.
5. Human audit from every domain/status stratum.
Any unexplained A/B disagreement blocks freeze.
## 3. Required mutations
Mutation suite MUST detect:
- supported ↔ refuted;
- unknown → false;
- conflict silently resolved;
- wrong version/scope;
- missing evidence;
- fabricated provenance;
- swapped arguments;
- wrong arity;
- skipped clarification;
- forbidden conclusion accepted.
## 4. Primary endpoint
Single primary endpoint:
```text
Exact Epistemic Contract Accuracy by base scenario
```
A scenario passes only under one preregistered paraphrase aggregation rule.
Example:
```text
scenario_pass = all mandatory paraphrases pass
```
Choose one rule before HOLDOUT and never change it afterwards.
## 5. Field scoring
Scorer MUST output individual booleans for:
```text
status
action
arguments
scope/version
clarification
provenance
forbidden conclusion
schema validity
```
Composite score is derived from these fields, never the reverse.
Malformed output, timeout and exhausted retry are incorrect outcomes.
## 6. Gold versus extracted decomposition
Always score separately:
```text
gold query -> runtime -> frame -> renderer
natural question -> extracted query -> runtime -> frame -> renderer
```
Required error buckets:
```text
source extraction
question interpretation
query formation
formal execution
policy
frame serialization
renderer
infrastructure
```
Never attribute extractor failure to solver.
## 7. Acceptable alternatives
When multiple queries or frames are semantically valid:
- enumerate alternatives before model runs;
- compare by semantic normal form where possible;
- never accept an alternative solely because model produced it;
- publish alternative-count and adjudication rule.
## 8. Scorer freeze
Before HOLDOUT record:
```text
oracle hash
scorer hash
semantic spec hash
mutation report
A/B differential report
human audit report
```
After HOLDOUT, scorer bug fixes require:
1. written bug description;
2. proof that no scientific choice changed;
3. version bump;
4. rerun of every affected mode;
5. publication of old and new scores.
## 9. STOP rules
STOP flagship route when:
- oracle independence cannot be demonstrated;
- mutation suite misses critical errors;
- scorer accepts leaked gold;
- A/B disagreements remain unresolved;
- result depends on post-hoc acceptable alternatives;
- composite result cannot be decomposed by error layer.
