# Generated package production runbook

Run these commands from the generated package root.

## Prepare environment

    Copy-Item .\deploy\production\.env.production.example .\deploy\production\.env.production
    notepad .\deploy\production\.env.production

Replace all __APPFORGE_SET_* sentinels before customer deployment.
Do not commit .env.production.

## Validate compose

    docker compose --env-file .\deploy\production\.env.production -f .\deploy\production\docker-compose.production.yml config --quiet

## Backup before migration

    New-Item -ItemType Directory -Force .\deploy\production\backups | Out-Null
    docker compose --env-file .\deploy\production\.env.production -f .\deploy\production\docker-compose.production.yml up -d db
    docker compose --env-file .\deploy\production\.env.production -f .\deploy\production\docker-compose.production.yml exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --file=/tmp/appforge.dump'
    docker compose --env-file .\deploy\production\.env.production -f .\deploy\production\docker-compose.production.yml cp db:/tmp/appforge.dump .\deploy\production\backups\appforge.dump

## Controlled migration

    docker compose --env-file .\deploy\production\.env.production -f .\deploy\production\docker-compose.production.yml --profile migrate run --rm api-migrate

A failed migration is a release stop.

## Optional seed

    docker compose --env-file .\deploy\production\.env.production -f .\deploy\production\docker-compose.production.yml --profile seed run --rm api-seed

## Start runtime

    docker compose --env-file .\deploy\production\.env.production -f .\deploy\production\docker-compose.production.yml up --build -d

## Smoke

    pwsh .\deploy\production\smoke.ps1 -PublicBaseUrl http://127.0.0.1:8080

## Restore

    docker compose --env-file .\deploy\production\.env.production -f .\deploy\production\docker-compose.production.yml up -d db
    docker compose --env-file .\deploy\production\.env.production -f .\deploy\production\docker-compose.production.yml cp .\deploy\production\backups\appforge.dump db:/tmp/appforge.dump
    docker compose --env-file .\deploy\production\.env.production -f .\deploy\production\docker-compose.production.yml exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists /tmp/appforge.dump'

## Rollback decision

Application rollback and database rollback are separate decisions.
Do not assume that an older package can use a database migrated by a newer package.
