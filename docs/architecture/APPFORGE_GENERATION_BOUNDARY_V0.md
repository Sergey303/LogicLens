# AppForge generation boundary v0

Status: accepted baseline for the Document Evidence Service generation trial.

## What AppForge currently provides

The current Markdown-to-EF contour generates a .NET 10 / EF Core 10 backend from a Markdown model.
Its production profile uses PostgreSQL by default and emits Npgsql-based DbContext registration,
entities, configurations, CRUD services, controllers, contracts, and a generation manifest.

The current generator still emits historical fixed project names such as
`GeneratedClinic.Persistence.csproj` and `GeneratedClinic.slnx`. Do not rename generated files by
hand. Generalizing generated project names belongs in AppForge, not in a consumer patch.

## What LogicLens uses

For the first service slice, AppForge owns only this replaceable contour:

```text
Markdown operational model
  -> generated EF Core entities/configuration
  -> generated PostgreSQL host and CRUD API
```

The source model is
[`services/document-evidence/spec/document-evidence.md`](../../services/document-evidence/spec/document-evidence.md).
Generated output belongs only under `services/document-evidence/Generated/`.

## What stays handwritten

AppForge output does not own:

- workspace and object-level authorization;
- upload quarantine, media signatures, or OOXML checks;
- immutable byte storage and storage-path policy;
- idempotent upload completion and processing orchestration;
- parser adapters or canonical document IR;
- page, sheet, section, cell, or fragment anchors;
- revocation and retrieval-index invalidation;
- source assertion acceptance, capsules, or active epochs;
- SWI-Prolog rules, decisions, or final answers.

Generated controllers remain an internal development surface until a handwritten access facade and
contract boundary are implemented.

## Generation command

Run the repository-owned wrapper:

```powershell
.\services\document-evidence\generate-appforge.ps1 `
  -AppForgeRoot D:\projects\ChatPilotGroup\AppForge
```

The wrapper:

1. requires a clean AppForge checkout unless explicitly overridden;
2. runs the production PostgreSQL generator;
3. verifies the generated manifest;
4. records AppForge commit and stable input/output hashes;
5. builds the generated solution unless `-SkipBuild` is supplied.

## Acceptance

The generation trial is accepted only when:

- output is reproducible from the same spec and AppForge commit;
- all generated files remain isolated under `Generated/`;
- no generated file is hand-edited;
- the manifest declares production and PostgreSQL;
- the generated solution builds;
- handwritten lifecycle code depends only on an explicit generated boundary.