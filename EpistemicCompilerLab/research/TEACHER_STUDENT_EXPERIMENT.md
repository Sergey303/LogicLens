# Codex→Qwen teacher loop measurement protocol

## Research question

Can a stronger remote teacher improve a fixed weak local model by compiling source-grounded knowledge and instructions, without exposing a closed holdout or changing student weights?

## System under test

- Teacher: Codex CLI authenticated with ChatGPT, account-default model unless an explicit supported identifier is recorded.
- Student: `qwen2.5-coder:7b` through a derived Ollama CPU profile.
- Executable knowledge: SWI-Prolog.
- Trusted components: case loader, scorer, candidate validator, Prolog regression tests and artifact packager.

This is prompt/representation optimization, not model training.

## Information boundary

Codex receives source evidence, the current prompt and Prolog representation, full labeled TRAIN diagnostics, and aggregate DEV metrics. It never receives DEV questions or labels during optimization. HOLDOUT is not evaluated until a winning epoch has been selected and is never sent to Codex.

The student receives only the candidate prompt, candidate Prolog text and one question. Expected values never enter the student request.

## Fixed pilot split

The pilot contains 18 source-grounded Russian questions: 6 TRAIN, 6 DEV and 6 HOLDOUT. It covers before/after-transition rules, a revision exception, unsupported revisions and missing required fields. The pilot is an engineering gate, not sufficient evidence for a paper by itself.

## Tracks and ablations

Run each track from the same baseline and with the same edit budget:

1. baseline: no teacher edits;
2. prompt-only;
3. prolog-only;
4. combined prompt+Prolog.

Do not compare a combined edit with a single-factor edit as if the causal factor were known.

## Epoch protocol

1. Evaluate the current candidate on TRAIN and DEV.
2. Store raw Qwen output before scoring.
3. Select the current best candidate by DEV exact accuracy, then TRAIN exact accuracy, then smaller total candidate bytes.
4. Give Codex TRAIN diagnostics and DEV aggregate metrics.
5. Validate the returned candidate against the permitted track, anti-memorization checks, Prolog syntax and the fixed regression suite.
6. Evaluate an accepted candidate as the next epoch.
7. Stop at the epoch budget, on `stop`, or after two accepted epochs without DEV improvement.
8. Evaluate HOLDOUT exactly once on the selected best candidate.

## Primary measurements

- exact case accuracy on TRAIN, DEV and HOLDOUT;
- action, status, material and clarification-field accuracy;
- generalization gap: TRAIN accuracy minus HOLDOUT accuracy;
- improvement over epoch 0;
- best epoch and epochs-to-best.

## Efficiency and audit measurements

- Qwen prompt and output tokens;
- per-case and total latency;
- Codex calls;
- accepted and rejected candidates;
- prompt bytes, Prolog bytes and total representation bytes;
- candidate change type and short hypothesis;
- tool-event audit and runner errors.

## Publication-grade extension

Before claiming general improvement:

- expand to at least 90 cases with frozen generation rules;
- use at least three independently generated paraphrase families;
- run at least three student seeds per track;
- repeat the complete experiment at least three times because the account-default Codex teacher may vary;
- report mean, standard deviation, confidence intervals and every failed/rejected epoch;
- include a static-rule baseline and direct-Codex upper bound;
- freeze hashes for source evidence, cases, prompts, Prolog baseline, model tags and scripts;
- predeclare the primary metric and stopping rule;
- keep a never-touched final holdout or external replication set.

## Interpretation limits

An improvement on this synthetic fixture shows that teacher-compiled instructions or representation helped this student under the recorded protocol. It does not establish model training, broad Russian-language improvement, industrial reliability or superiority on unrelated domains.
