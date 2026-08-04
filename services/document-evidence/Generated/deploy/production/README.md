# AppForge packaged production deploy preset

Model: Document Evidence Operational Model
Backend project: DocumentEvidenceOperationalModel.Persistence

This directory is a self-contained P0 single-VPS Docker Compose preset for this generated package.
Run all commands from the generated package root.

## Services

- PostgreSQL
- generated ASP.NET API
- generated static React/PrimeReact admin app
- public reverse proxy
- one-off migration service
- one-off seed service

## Important boundary

Normal API startup does not apply migrations or seed data automatically.
Use the explicit api-migrate and api-seed profiles from RUNBOOK.md.
The public HTTP endpoint is intended to sit behind an outer TLS/WAF layer for customer production deployment.
