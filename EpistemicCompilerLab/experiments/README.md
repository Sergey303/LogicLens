# Epistemic Compiler Lab experiment protocol

Each experiment compares one controlled change to a fixed baseline.

## Version identity

Record:

- LogicLens Git commit;
- student model and quantisation;
- teacher model or teacher pipeline;
- student prompt path and hash;
- teacher prompt path and hash;
- case-set version;
- SWI-Prolog version;
- changed layer.

## Primary comparisons

1. original Markdown in context;
2. compact JSON without execution;
3. Prolog text interpreted mentally by the student;
4. student using SWI-Prolog CLI;
5. CLI plus optional evidence and exception tails;
6. teacher-guided correction after student errors.

## Metrics

- correct final answers;
- correct `unknown` decisions;
- semantic query errors;
- Prolog execution errors;
- number of CLI calls;
- number of optional tails opened;
- input and output tokens;
- elapsed time;
- evidence coverage;
- regressions on neighbouring cases;
- manual corrections required.

## Change isolation

Prefer one changed layer per run:

- facts;
- rules;
- learner representation;
- student prompt;
- teacher prompt;
- user translator;
- model or adapter;
- question-selection policy.

A combined change is allowed only when interaction between layers is the explicit experiment.

## Minimal run record

Store future run records as JSONL:

```json
{"runId":"run-001","commit":"<sha>","studentModel":"<model>","changedLayer":"rules","cases":10,"correct":9,"unknownCorrect":1,"cliCalls":12,"openedTails":3,"notes":"Added revision condition"}
```

Do not commit private prompts, secrets, raw customer documents or machine-local paths.