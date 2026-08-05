# Submission and Review Protocol
Статус: **MUST complete before TMLR submission**
## 1. Preregistration
Before opening HOLDOUT commit and hash:
```text
claims and hypotheses
primary endpoint/contrast
smallest effect
power analysis
models/modes
retry/exclusion rules
oracle/scorer/analysis hashes
table shells
STOP/pivot rules
```
No scientific-choice edits afterwards.
## 2. HOLDOUT ceremony
Execute exactly:
1. Verify immutable commit.
2. Verify sealed hashes.
3. Verify model/runtime hashes.
4. Run deterministic tests.
5. Create signed run manifest.
6. Execute blocked randomized batch.
7. Store raw outputs before scoring.
8. Score with frozen scorer.
9. Generate completeness report.
10. Archive immutable artifact.
Do not inspect partial scores.
Global infrastructure rerun applies to complete affected block only under preregistered rule.
## 3. Replication
Replication MUST differ in:
- source family;
- rule templates;
- entity families;
- wording/paraphrase source.
Never tune on replication. Report it separately before pooled analysis.
## 4. Red-team claims audit
For every abstract sentence record:
```text
claim
strongest alternative explanation
control
result
remaining limitation
retain/narrow/delete
```
Mandatory attacks:
- answer copying;
- solver-versus-no-solver triviality;
- synthetic-only data;
- oracle circularity;
- leakage;
- one-model effect;
- hidden teacher advantage;
- unfair token budget;
- deterministic renderer superiority;
- extraction domination.
Unresolved Blocker deletes or narrows claim.
## 5. Manuscript evidence
Every numerical claim points to:
```text
table/figure
metric
split
models
CI/uncertainty
analysis artifact
```
Main text MUST report negative results, failures, strongest baseline, gold/extracted decomposition, deterministic renderer, heterogeneity, replication and limitations.
## 6. Abstract language
Forbidden:
- learned Prolog;
- guaranteed privacy;
- universally reliable;
- formal proof of source truth;
- model weights trained;
- pilot as publication-grade proof.
Use bounded wording tied to tested contracts/models/domains.
## 7. Anonymous artifact
Create separate snapshot. Remove:
- usernames and repository URLs;
- local paths;
- author metadata;
- issues/PRs;
- private organization data;
- credentials.
Retain:
- licenses;
- hashes;
- commands;
- raw outputs/failures;
- prompts/schemas;
- oracle/scorer;
- analysis;
- lockfiles.
Run identity and secret scan.
## 8. Clean-room reproduction
Independent environment MUST:
1. install from instructions;
2. run deterministic tests;
3. reproduce one public model subset;
4. regenerate primary tables from stored outputs;
5. report undocumented steps.
Submission blocked until undocumented steps are zero.
## 9. Current TMLR check
Immediately before submission verify official current:
- scope/criteria;
- double blind;
- supplementary rules;
- LLM disclosure;
- OpenReview profiles;
- conflicts/quota;
- concurrent submission.
Record date and sources.
## 10. Review response
For each comment classify:
```text
factual
clarification
analysis
experiment
scope disagreement
invalid request
```
Answer:
1. acknowledge exact concern;
2. state evidence;
3. make change or principled refusal;
4. cite revision location.
New experiments apply symmetrically, never only to favorable subsets.
## 11. Submission STOP rules
Do not submit when:
- replication absent/contradictory without narrowing;
- primary effect loses to matched baseline;
- oracle independence unproven;
- leakage audit incomplete;
- deterministic renderer missing;
- anonymous artifact identifies authors;
- clean-room reproduction fails;
- abstract sentence lacks PASS evidence;
- unresolved Blocker remains.
