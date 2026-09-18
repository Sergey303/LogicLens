# Builder task: researcher at IIS

Produce one LogicLens epoch-candidate-v0 proposal for the task in `task.json`.

You receive only the frozen task, generated evidence responses, the candidate schema, and these instructions. Treat every identifier and FactId as data. Do not invent facts that are absent from the evidence.

## Mandatory language boundary

Every file whose name ends in `.pl` is **SWI-Prolog source**, never Perl.

The candidate is invalid if it contains Perl constructs such as:

```text
#!/usr/bin/perl
use strict
use warnings
sub
my
=>
```

Use ordinary SWI-Prolog clauses, atoms, variables, lists, module declarations and plunit tests.

The rule file must follow this structural contract:

```prolog
:- module(ModuleName, [predicate_name/2]).
:- use_module('../data/epoch_data.pl').

predicate_name(Person, EvidenceFactIds) :-
    epoch_data:fact(FactIdA, Subject, PredicateIriA, iri(ResourceIri)),
    epoch_data:fact(FactIdB, Subject, PredicateIriB, literal("text", lang('ru'))),
    sort([FactIdA, FactIdB], EvidenceFactIds).
```

The example above defines syntax only. Select the real predicates, resources, variables and evidence from the frozen task and public evidence. Do not copy placeholder identifiers into the candidate.

The test file must be executable SWI-Prolog plunit source:

```prolog
:- begin_tests(ModuleName).
:- use_module('../rules/candidate_researcher_at_iis.pl').

test(test_name) :-
    Goal,
    assertion(Condition).

:- end_tests(ModuleName).
```

The UI file is JSON, not Prolog and not prose. It must have this contract:

```json
{
  "schemaVersion": "0.1",
  "bindings": [
    {
      "predicate": "the exact task-declared UI predicate",
      "component": "the exact task-declared trusted component"
    }
  ]
}
```

## Required proposal files

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
