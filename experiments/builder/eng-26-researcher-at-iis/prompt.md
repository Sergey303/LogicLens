# Builder task: researcher at IIS

Produce one LogicLens epoch-candidate-v0 proposal for the task in `task.json`.

You receive only the frozen task, generated evidence responses, the candidate schema, and these instructions. Treat every identifier and FactId as data. Do not invent facts that are absent from the evidence.

Your proposal must contain exactly the three task-declared files:

```text
rules/candidate_researcher_at_iis.pl
tests/candidate_researcher_at_iis_tests.pl
ui/researcher-at-iis.json
```

The rule module must export:

```prolog
researcher_at_iis(Person, EvidenceFactIds)
```

The predicate must derive a result through one participation resource. It must use the canonical fact predicates from `epoch_data`, require IIS as the organization, require the Russian `исследователь` role literal, and return the three supporting FactId values in stable sorted order.

Write meaningful executable tests. The UI file must use only the trusted component specified by the task. Do not provide shell commands, paths outside the proposal, activation instructions, active-file edits, or prose in place of files.

Return or write a complete proposal directory conforming to `epoch-candidate-v0.schema.json`. Provider-specific wrappers may record run metadata, but they may not change the task or validator.
