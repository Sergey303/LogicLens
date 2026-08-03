# Personal Knowledge World v0

Status: proposed architecture baseline  
First domain: `management`

## Definition

A Personal Knowledge World is a domain repository containing reusable knowledge capsules, learning modules, role tracks, sources, semantic registries and learner-independent scenarios.

The world is content. LogicLens is the engine.

```text
LogicLens
  contracts
  source preparation
  capsule compiler
  SWI-Prolog execution
  evaluation runtime
  generic prompts
  deterministic packaging

Domain repository
  world manifest
  semantic model
  sources and licences
  prepared data
  capsules
  modules
  scenarios
  rubrics
```

## World layout

```text
worlds/<world-id>/
  world.json
  semantic/
    vocabulary.json
    predicates.json
    roles.json
    competencies.json
  capsules/
    <capsule-id>/
  modules/
    <module-id>/
```

The semantic model is intentionally lighter than a full OWL ontology and stronger than free-form tags. It uses typed registries that may evolve independently:

- vocabulary and concept kinds;
- predicate signatures and value spaces;
- roles and ownership boundaries;
- competencies and evidence artefacts.

## Management world

The first management world supports five tracks:

- Team Lead;
- Engineering Manager;
- Project or Delivery Manager;
- Product Manager;
- CTO.

The first capsule is `management.role-boundaries`. The first module is `management.module.role-boundaries`.

The initial shared scenario asks each role to respond to the same launch crisis. Differences in expected decisions expose whether a learner understands role ownership rather than only management terminology.

## Source policy

Open and internal sources are represented through a source manifest.

- Open sources may be linked or snapshotted according to their licence.
- Restricted books and paid courses are bibliographic references only.
- Repository-owned course materials may be referenced directly.
- Every prepared assertion must point to a source ID.
- Organisation-specific practices are marked `context-dependent`.

## Learning run boundary

Capsules and modules never contain personal learner state. A learning run stores:

- selected track and module;
- issued scenario state;
- learner submission;
- rubric evidence;
- review and mandatory corrections;
- final result;
- links to produced artefacts.

This allows the same world and capsule package to be reused by many learners without changing the knowledge package.

## First vertical slice

The first slice is successful when:

1. `world.json`, capsule and module manifests validate;
2. prepared assertions compile into canonical Prolog facts;
3. provenance source IDs resolve;
4. the package builds twice with the same hash;
5. package verification detects a changed file;
6. the role-boundary module can be issued in Markdown/JSON form;
7. at least one supported, opposed, unknown and conflicting role claim is represented in tests.
