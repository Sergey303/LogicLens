# WP-006 — Multiplicity, failures and missingness

Status: producer design candidate; pre-HOLDOUT.

## 1. One primary confirmatory contrast

The flagship claim has exactly one primary confirmatory contrast: preregistered authoritative semantic-result placement versus one preregistered matched fixed-weight baseline on identical cases.

The primary two-sided familywise alpha is `0.05`. WP-006 does not permit choosing whichever comparator gives the largest DEV or HOLDOUT difference and calling that comparison primary.

Any additional comparator/ablation effects are secondary. If inferential p-values are reported for a declared secondary family, apply Holm step-down at familywise alpha `0.05`. Exploratory analyses are labelled exploratory and are not substitutes for the primary result.

Field-level scorer booleans are diagnostic secondary outcomes. The primary endpoint remains the frozen publication composite correctness from WP-005.

## 2. Paired case retention

A primary pair exists only when the same frozen benchmark case was assigned to both primary arms under the same preregistered evaluation contract.

The following are **not ordinary missing data** and are scored incorrect according to the experiment contract when attributable to the evaluated system/run:

- malformed model output;
- forbidden tool use;
- exhausted model/provider retry under the frozen execution policy;
- parser/schema failure caused by the response;
- timeout/resource failure attributed to the evaluated response path when the infrastructure contract classifies it as a run failure.

They cannot be dropped merely because retaining them hurts an arm.

## 3. Truly non-evaluable cases

A case may be excluded from the paired primary denominator only for a reason that makes the case scientifically non-evaluable independently of arm performance, for example:

- benchmark packet corruption proven before scoring;
- scorer/oracle artifact corruption affecting both arms and requiring benchmark re-versioning;
- duplicate case discovered by the frozen deduplication rule;
- source withdrawal/legal unavailability occurring before outcome inspection;
- infrastructure outage that prevented **both** paired arm executions and is classified as external infrastructure rather than model behavior.

Every exclusion requires a predeclared reason code and is retained in an attrition ledger. The exclusion rule is symmetric across arms.

A one-arm external infrastructure failure does not automatically permit dropping the pair. The execution protocol must first apply its frozen retry/recovery rule. If the pair cannot be completed without changing the scientific contract, the case enters the non-evaluable ledger with an explicit paired-incompleteness reason and counts against the `5%` planning attrition allowance.

## 4. Power and attrition

Primary planning reserves `5%` non-evaluable attrition. Sensitivity reports `0%`, `5%`, and `10%`.

If the frozen confirmatory case inventory cannot supply the required eligible N **after** the preregistered attrition allowance, the power gate fails before HOLDOUT. The experiment may collect more eligible cases or version a new design; it may not lower target power, change SESOI, or redefine failures as missing to make the gate pass.

Observed attrition higher than planned is reported and included in sensitivity analysis. It does not authorize post hoc endpoint or denominator changes.

## 5. Cluster count

`source_family_id` is the primary dependence cluster. The asymptotic cluster-robust primary analysis requires at least `30` independent source-family clusters after exclusions.

If fewer than 30 remain, the current asymptotic primary-analysis contract is not eligible for confirmatory PASS. A finite-cluster method may be proposed only as a new preregistered version before confirmatory scoring; it is not selected after seeing significance.

## 6. No optional stopping

There is no significance-based interim stopping, sample-size extension, or repeated peeking. The only permitted sample-size update is the once-only blinded nuisance update in `BLINDED_NUISANCE_UPDATE_PROTOCOL.json`, which cannot reveal the signed treatment effect and cannot change SESOI, alpha, target power, endpoint, or primary contrast.
