# Deploy Automático + Backups — Diseño

## Objetivo

Sistema de deploy automático desde GitHub Actions al VPS via SSH, con backups programados de PostgreSQL.

## Deploy

**Trigger:** Push a `main` (después de merge de PR).

**Flujo:**
1. GitHub Actions ejecuta CI (lint + test)
2. Si pasa, conecta por SSH al VPS
3. Ejecuta `scripts/deploy.sh` en el VPS

**`scripts/deploy.sh`:**
1. Backup pre-deploy de la DB → `/opt/backups/consul_app/manual/`
2. `git pull origin main`
3. `docker compose -f docker-compose.prod.yml up -d --build`
4. Aplica migraciones + ensure-admin
5. `docker image prune -f`

**GitHub Secrets requeridos:**
- `VPS_SSH_KEY` — clave privada SSH
- `VPS_HOST` — IP o dominio del VPS
- `VPS_USER` — usuario SSH
- `VPS_DEPLOY_PATH` — ruta al repo en el VPS

## Backups de PostgreSQL

**Semanales (automáticos):**
- Cron: viernes a las 21:00
- Ruta: `/opt/backups/consul_app/auto/`
- Retención: máximo 4 (al crear el 5to se elimina el más antiguo)

**Pre-deploy (manuales):**
- Se ejecutan automáticamente antes de cada deploy
- Ruta: `/opt/backups/consul_app/manual/`
- Retención: máximo 4 (al crear el 5to se elimina el más antiguo)

**Script:** `scripts/backup-db.sh <auto|manual>`
- Ejecuta `pg_dump` dentro del contenedor Postgres
- Comprime con gzip
- Nombre: `consul_app_YYYY-MM-DD_HH-MM.sql.gz`
- Rota backups según el límite de 4 por directorio

## Setup inicial del VPS (una sola vez)

1. Generar par de claves SSH y configurar `authorized_keys`
2. Crear directorios: `/opt/backups/consul_app/auto` y `/opt/backups/consul_app/manual`
3. Configurar cron para backup semanal
4. Cambiar remote del repo de HTTPS a SSH (o configurar PAT para HTTPS)
5. Agregar secrets en GitHub repo settings
