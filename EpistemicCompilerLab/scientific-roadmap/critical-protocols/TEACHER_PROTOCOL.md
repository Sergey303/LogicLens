# Teacher Protocol
Статус: **MUST follow for Codex and every alternative teacher**
## 1. Isolated tracks
Allowed tracks:
```text
prompt-only
program-only
schema-only when preregistered
combined only as secondary ablation
```
One candidate may change only the declared artifact class.
## 2. Teacher-visible information
Teacher MAY receive:
- labeled TRAIN diagnostics;
- current allowed artifact;
- aggregate DEV metrics;
- previous accepted/rejected effects;
- fixed tool and token budget.
Teacher MUST NOT receive:
- DEV questions/answers;
- HOLDOUT;
- REPLICATION;
- private production `R`;
- arbitrary shell;
- sealed paths;
- hidden expected fields outside TRAIN;
- benchmark IDs as hints.
Tooling, not prompt text, must enforce the boundary.
## 3. Fixed budget
Before the first epoch record:
```text
max epochs
max calls
max input tokens
max output tokens
max wall-clock
allowed tools
```
Do not expand budget because early candidates fail.
Comparisons across teachers must report matched or normalized budgets.
## 4. Required candidate record
Every proposal MUST include:
```text
track
hypothesis
reproduced TRAIN failure
earliest faulty layer
exact diff
expected effect
regression risk
tests to run
teacher usage
```
Proposal without a falsifiable hypothesis is rejected.
## 5. Candidate acceptance
Apply in strict order:
1. schema validation;
2. anti-memorization scan;
3. deterministic tests;
4. Prolog regressions;
5. TRAIN evaluation;
6. aggregate DEV selection;
7. complexity tie-break.
Rejected candidate never reaches HOLDOUT.
## 6. Frozen selection rule
Use one deterministic rule, for example:
```text
maximize DEV primary metric
then maximize TRAIN primary metric
then minimize artifact size
then retain earlier epoch
```
Freeze exact rule before teacher runs.
Teacher never sees case-level DEV effects.
## 7. Human and teacher baselines
MUST include:
- original baseline;
- Codex condition;
- documented human-designed condition;
- second teacher when technically feasible.
Closed account-default Codex is never the sole evidence for general teacher claims.
Record exact CLI/runtime/date and audit events.
## 8. Anti-memorization
Reject candidate containing:
- case IDs;
- full benchmark questions;
- expected answer lists;
- entity-specific lookup tables without domain justification;
- branches keyed to TRAIN wording;
- unusually long literal fragments from cases.
Run lexical and semantic similarity scans against TRAIN.
## 9. Stop optimization
Stop teacher loop when any holds:
- epoch budget exhausted;
- no candidate passes validation;
- two accepted epochs produce no DEV gain;
- improvement requires case-specific encoding;
- regression risk exceeds preregistered threshold;
- teacher repeats same mechanism without new evidence.
Do not continue until a positive result appears.
## 10. Reporting
Publish:
- all accepted/rejected proposals;
- infrastructure failures;
- token/call usage;
- selection decisions;
- TRAIN/aggregate DEV effects;
- unchanged baseline result.
Do not describe zero-effect teacher edits as student learning.
