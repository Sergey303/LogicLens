# AppForge generated admin production package

Generated at UTC: 2026-08-04T12:33:48.9676450Z

## Source

- Spec: D:\projects\ChatPilotGroup\WorkTrees\LogicLens-shared-document-service\services\document-evidence\spec\document-evidence.md
- Spec SHA-256: eda92de5c6baca45923a6875dfd6ed4b7cefe68d64d0ac6001269ab42007c5c7
- Model: Document Evidence Operational Model
- Project: DocumentEvidenceOperationalModel.Persistence
- Runtime profile: production
- Generator: AppForge.MdToDomain 0.1.0

## Package structure

```text
backend/           Generated .NET backend, solution, preserved EF migration chain, and idempotent migration-chain SQL.
backend-contract/  Canonical backend-contract JSON artifacts.
frontend/          Generated TypeScript bindings and React/PrimeReact components/pages.
frontend-app/      Production Vite app and deployable static bundle under dist/.
deploy/            Self-contained single-VPS Docker Compose production preset.
manifest/          Package manifest and backend-contract generator config.
docs/              Package-local runbook and delivery notes.
```

## Verification

```powershell
dotnet build "D:\projects\ChatPilotGroup\WorkTrees\LogicLens-shared-document-service\services\document-evidence\Generated\backend\DocumentEvidenceOperationalModel.Persistence.csproj"
Test-Path "D:\projects\ChatPilotGroup\WorkTrees\LogicLens-shared-document-service\services\document-evidence\Generated\backend\DocumentEvidenceOperationalModel.slnx"
Test-Path "D:\projects\ChatPilotGroup\WorkTrees\LogicLens-shared-document-service\services\document-evidence\Generated\backend\Migrations\AppForgeGeneratedMigrations.idempotent.sql"
Test-Path "D:\projects\ChatPilotGroup\WorkTrees\LogicLens-shared-document-service\services\document-evidence\Generated\backend-contract\meta\domains.json"
Test-Path "D:\projects\ChatPilotGroup\WorkTrees\LogicLens-shared-document-service\services\document-evidence\Generated\frontend\runtime\httpClient.ts"
Test-Path "D:\projects\ChatPilotGroup\WorkTrees\LogicLens-shared-document-service\services\document-evidence\Generated\frontend-app\dist\index.html"
Test-Path "D:\projects\ChatPilotGroup\WorkTrees\LogicLens-shared-document-service\services\document-evidence\Generated\deploy\production\docker-compose.production.yml"
Test-Path "D:\projects\ChatPilotGroup\WorkTrees\LogicLens-shared-document-service\services\document-evidence\Generated\deploy\production\.env.production.example"
Test-Path "D:\projects\ChatPilotGroup\WorkTrees\LogicLens-shared-document-service\services\document-evidence\Generated\manifest\package-manifest.json"
```

The package was generated from an explicit SpecPath. No fixture-specific project or assembly name is assumed by the pipeline.
