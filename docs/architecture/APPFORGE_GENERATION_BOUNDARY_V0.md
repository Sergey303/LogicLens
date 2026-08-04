# AppForge generation boundary v0

Status: accepted baseline for the Document Evidence Service generation trial.

## Current AppForge capability

AppForge now generates a complete model-driven production admin package from Markdown:

```text
Markdown subject model
  -> .NET 10 / EF Core 10 backend
  -> PostgreSQL/Npgsql runtime and EF migrations
  -> canonical backend-contract JSON
  -> domain-scoped TypeScript bindings
  -> React/PrimeReact components and pages
  -> production Vite app and static dist
  -> Docker Compose deploy preset
```

Project, solution, assembly, DbContext, and database names are derived from the model identity and
recorded in the generated manifest. LogicLens must not assume historical `GeneratedClinic` names.

## What LogicLens generates

The source model is
[`services/document-evidence/spec/document-evidence.md`](../../services/document-evidence/spec/document-evidence.md).
The complete generated package belongs under `services/document-evidence/Generated/`:

```text
Generated/
  backend/
  backend-contract/
  frontend/
  frontend-app/
  deploy/
  manifest/
  docs/
```

AppForge owns this replaceable operational contour:

- EF Core entities, configuration, migrations, and CRUD services;
- internal CRUD controllers and canonical JSON contract;
- generated TypeScript bindings and HTTP runtime;
- generated React/PrimeReact administration components and pages;
- production Vite bundle and deployment preset.

The generated UI is an internal operations/admin surface. It is not the final product UX and does
not replace the public Document Evidence Service facade.

## What stays handwritten

AppForge output does not own:

- workspace and object-level authorization policy;
- upload quarantine, media signatures, or OOXML checks;
- immutable byte storage and storage-path policy;
- idempotent upload completion and durable processing orchestration;
- parser adapters or canonical document IR;
- page, sheet, section, cell, or fragment anchors;
- revocation and retrieval-index invalidation;
- public service commands, download plans, or cross-service authorization;
- source assertion acceptance, capsules, active epochs, or SWI-Prolog decisions;
- final product screens and evidence-oriented interaction design.

LogicLens and EngDoc Essential use a versioned handwritten service facade and generated clients.
They do not call generated CRUD endpoints directly or read the service database/blob paths.

## Generation command

Run the repository-owned wrapper:

```powershell
.\services\document-evidence\generate-appforge.ps1 `
  -AppForgeRoot D:\projects\ChatPilotGroup\AppForge
```

The wrapper:

1. requires a clean AppForge checkout unless explicitly overridden;
2. runs the full production package generator against the LogicLens Markdown model;
3. verifies model-driven identity and required backend/JSON/TS/React/deploy artifacts;
4. records the exact AppForge commit and stable input/package hashes;
5. preserves an earlier migration chain when `-PreviousPackageRoot` is supplied.

## Generated and handwritten dependency rule

Generated frontend code may depend on generated contract/runtime packages. Handwritten product code
may compose generated resource components through explicit adapters. Generated code must never
import handwritten product features, parser implementations, storage policy, or LogicLens runtime.

The generated output remains output: never use generated JSON, TypeScript, or React files as the
hand-edited source for the next generator step.

## Acceptance

The generation trial is accepted only when:

- output is reproducible from the same spec and AppForge commit;
- all generated files remain isolated under `Generated/`;
- no generated file is hand-edited;
- the package manifest records production, model identity, and all output roots;
- backend, migration SQL, canonical JSON, TypeScript, React/PrimeReact, Vite dist, and deploy preset exist;
- the AppForge production package runner completes its build and verification gates;
- handwritten lifecycle code depends only on explicit generated/public boundaries.
