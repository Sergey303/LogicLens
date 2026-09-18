# Builder task: researcher at IIS

Produce one LogicLens epoch-candidate-v0 proposal for the task in `task.json`.

You receive only the frozen task, generated evidence responses, the candidate schema, and these instructions. Treat every identifier and FactId as data. Do not invent facts that are absent from the evidence.

## Structured provider response

Follow the exact JSON response schema that appears after the public evidence. When that schema asks for a `selection` object, return only the three requested public FactIds. Do not write the Prolog, PlUnit or UI files yourself: the trusted adapter will validate the selected facts and render the three task-declared files deterministically.

The selected participant, organization and role facts must be distinct, must all exist in the public evidence, and must use one identical participation Subject.

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

Use ordinary SWI-Prolog clauses, atoms, variables, strings, lists, module declarations and plunit tests.

## Exact fact tuple direction

Read every evidence fact and every `epoch_data:fact/4` call in this exact order:

```prolog
epoch_data:fact(FactId, Subject, Predicate, Object)
```

For this task, one shared participation resource is the **Subject** of all three required facts. The person, IIS organization and Russian role literal are Objects:

```prolog
epoch_data:fact(FParticipant, Participation,
                'http://fogid.net/o/participant', iri(Person)),
epoch_data:fact(FOrganization, Participation,
                'http://fogid.net/o/in-org', iri('urn:logiclens:org:iis')),
epoch_data:fact(FRole, Participation,
                'http://fogid.net/o/role',
                literal("исследователь", lang('ru')))
```

The lexical value of a language literal is a SWI-Prolog string in double quotes. It is not a single-quoted atom.

Do not reverse these edges. In particular, do not put `Person` or `urn:logiclens:org:iis` in the Subject position of the `participant` or `in-org` facts.

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

The test file must be executable SWI-Prolog plunit source.

Only these test-file lines are directives and start with `:-`:

- `:- begin_tests(ModuleName).`
- `:- use_module('../rules/candidate_researcher_at_iis.pl').`
- `:- end_tests(ModuleName).`

A plunit test case is an ordinary clause. It starts with `test(...)`, **without** `:-`. Never write `:- test(...)`.

At least one `test(...)` clause must appear after `begin_tests/use_module` and before `end_tests`. Closing the suite before the test creates an empty invalid suite.

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
