# Deploy Automático + Backups — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Sistema de deploy automático via GitHub Actions + SSH al VPS, con backups semanales y pre-deploy de PostgreSQL.

**Architecture:** GitHub Actions se conecta por SSH al VPS y ejecuta un deploy script que hace backup, pull, rebuild y migraciones. Un script de backup independiente se usa tanto desde cron (semanal) como desde el deploy (pre-deploy). Ambos con rotación de máximo 4 archivos por directorio.

**Tech Stack:** GitHub Actions, SSH, Bash, Docker Compose, pg_dump, gzip, cron

---

### Task 1: Script de backup de PostgreSQL

**Files:**
- Create: `scripts/backup-db.sh`

**Step 1: Crear el script de backup**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/backup-db.sh <auto|manual> [project_dir]
# Backs up PostgreSQL from the running Docker container.
# Keeps max 4 backups per directory, deletes oldest when exceeded.

TYPE="${1:-}"
PROJECT_DIR="${2:-$(cd "$(dirname "$0")/.." && pwd)}"

if [[ "$TYPE" != "auto" && "$TYPE" != "manual" ]]; then
    echo "Usage: $0 <auto|manual> [project_dir]"
    exit 1
fi

BACKUP_DIR="/opt/backups/consul_app/${TYPE}"
COMPOSE="docker compose -f ${PROJECT_DIR}/docker-compose.prod.yml"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M")
FILENAME="consul_app_${TIMESTAMP}.sql.gz"
MAX_BACKUPS=4

mkdir -p "$BACKUP_DIR"

# Get DB credentials from running container
DB_USER=$($COMPOSE exec -T db printenv POSTGRES_USER 2>/dev/null || echo "consul")
DB_NAME=$($COMPOSE exec -T db printenv POSTGRES_DB 2>/dev/null || echo "consul_app")

echo "[backup] Starting ${TYPE} backup..."
$COMPOSE exec -T db pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "${BACKUP_DIR}/${FILENAME}"

if [[ ! -s "${BACKUP_DIR}/${FILENAME}" ]]; then
    echo "[backup] ERROR: Backup file is empty, removing"
    rm -f "${BACKUP_DIR}/${FILENAME}"
    exit 1
fi

SIZE=$(du -h "${BACKUP_DIR}/${FILENAME}" | cut -f1)
echo "[backup] Created: ${BACKUP_DIR}/${FILENAME} (${SIZE})"

# Rotate: keep only MAX_BACKUPS, delete oldest
BACKUP_COUNT=$(ls -1 "${BACKUP_DIR}"/consul_app_*.sql.gz 2>/dev/null | wc -l)
if [[ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]]; then
    EXCESS=$((BACKUP_COUNT - MAX_BACKUPS))
    ls -1t "${BACKUP_DIR}"/consul_app_*.sql.gz | tail -n "$EXCESS" | while read -r old; do
        echo "[backup] Rotating out: $(basename "$old")"
        rm -f "$old"
    done
fi

echo "[backup] Done. ${TYPE} backups: $(ls -1 "${BACKUP_DIR}"/consul_app_*.sql.gz 2>/dev/null | wc -l)/${MAX_BACKUPS}"
```

**Step 2: Hacer el script ejecutable y verificar sintaxis**

Run: `chmod +x scripts/backup-db.sh && bash -n scripts/backup-db.sh`
Expected: Sin errores

**Step 3: Commit**

```bash
git add scripts/backup-db.sh
git commit -m "feat: add PostgreSQL backup script with rotation"
```

---

### Task 2: Script de deploy

**Files:**
- Create: `scripts/deploy.sh`

**Step 1: Crear el deploy script**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/deploy.sh
# Runs on the VPS. Pulls latest code, rebuilds containers, applies migrations.

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="docker compose -f ${PROJECT_DIR}/docker-compose.prod.yml"

cd "$PROJECT_DIR"

echo "=========================================="
echo "[deploy] Starting deploy at $(date)"
echo "=========================================="

# Step 1: Pre-deploy backup
echo "[deploy] Creating pre-deploy backup..."
bash "${PROJECT_DIR}/scripts/backup-db.sh" manual "$PROJECT_DIR" || {
    echo "[deploy] WARNING: Pre-deploy backup failed, continuing anyway"
}

# Step 2: Pull latest code
echo "[deploy] Pulling latest code..."
git pull origin main

# Step 3: Rebuild and restart containers
echo "[deploy] Building and restarting containers..."
$COMPOSE up -d --build

# Step 4: Wait for DB to be ready
echo "[deploy] Waiting for database..."
$COMPOSE exec -T db sh -lc 'until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; do sleep 1; done'

# Step 5: Apply migrations
echo "[deploy] Applying migrations..."
$COMPOSE exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"'
$COMPOSE exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"'
$COMPOSE exec -T app flask --app wsgi.py db upgrade
$COMPOSE exec -T app flask --app wsgi.py ensure-admin

# Step 6: Cleanup old Docker images
echo "[deploy] Cleaning up old images..."
docker image prune -f

echo "=========================================="
echo "[deploy] Deploy completed at $(date)"
echo "=========================================="
```

**Step 2: Hacer ejecutable y verificar sintaxis**

Run: `chmod +x scripts/deploy.sh && bash -n scripts/deploy.sh`
Expected: Sin errores

**Step 3: Commit**

```bash
git add scripts/deploy.sh
git commit -m "feat: add deploy script with pre-deploy backup"
```

---

### Task 3: GitHub Actions workflow de deploy

**Files:**
- Create: `.github/workflows/deploy.yml`

**Step 1: Crear el workflow**

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  ci:
    name: CI
    uses: ./.github/workflows/ci.yml

  deploy:
    name: Deploy to VPS
    needs: ci
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd ${{ secrets.VPS_DEPLOY_PATH }}
            bash scripts/deploy.sh
```

**Step 2: Verificar que ci.yml sea reutilizable**

El workflow actual `ci.yml` usa `on: push` y `on: pull_request`. Para poder reutilizarlo con `uses:`, necesita agregar `workflow_call` al trigger. Modificar `.github/workflows/ci.yml`:

Agregar al bloque `on:`:
```yaml
on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main, dev]
  workflow_call:
```

**Step 3: Commit**

```bash
git add .github/workflows/deploy.yml .github/workflows/ci.yml
git commit -m "feat: add deploy workflow triggered on push to main"
```

---

### Task 4: Makefile targets para deploy y backup

**Files:**
- Modify: `Makefile`

**Step 1: Agregar targets al Makefile**

Agregar al final del Makefile, antes del último bloque de prod targets (o al final):

```makefile
# ── Deploy & Backups ──────────────────────────────
backup-auto: ## Ejecuta backup automatico de la DB (produccion)
	bash scripts/backup-db.sh auto

backup-manual: ## Ejecuta backup manual/pre-deploy de la DB (produccion)
	bash scripts/backup-db.sh manual

deploy: ## Ejecuta deploy en el VPS (uso local)
	bash scripts/deploy.sh
```

Agregar los nuevos targets a la lista `.PHONY`.

**Step 2: Verificar**

Run: `make help`
Expected: Los nuevos targets aparecen en la lista

**Step 3: Commit**

```bash
git add Makefile
git commit -m "feat: add deploy and backup Makefile targets"
```

---

### Task 5: Documentación de setup del VPS

**Files:**
- Create: `docs/VPS_SETUP.md`

**Step 1: Crear documentación de setup**

```markdown
# Setup del VPS para Deploy Automático

## 1. Configurar SSH

En el VPS:
```bash
# Generar clave SSH (si no existe)
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy -N ""

# Agregar al authorized_keys
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Mostrar la clave privada (copiar para GitHub Secrets)
cat ~/.ssh/github_deploy
```

## 2. Configurar GitHub Secrets

En GitHub → Settings → Secrets and variables → Actions, agregar:

| Secret | Valor |
|--------|-------|
| `VPS_SSH_KEY` | Contenido de `~/.ssh/github_deploy` (clave privada) |
| `VPS_HOST` | IP o dominio del VPS |
| `VPS_USER` | Usuario SSH del VPS |
| `VPS_DEPLOY_PATH` | Ruta al repo (ej: `/opt/consul_app`) |

## 3. Crear directorios de backup

```bash
sudo mkdir -p /opt/backups/consul_app/auto
sudo mkdir -p /opt/backups/consul_app/manual
sudo chown -R $(whoami):$(whoami) /opt/backups/consul_app
```

## 4. Configurar cron para backup semanal

```bash
crontab -e
```

Agregar:
```
0 21 * * 5 /ruta/al/repo/scripts/backup-db.sh auto /ruta/al/repo >> /var/log/consul_backup.log 2>&1
```

## 5. Configurar git remote

Cambiar de HTTPS a SSH (recomendado):
```bash
cd /ruta/al/repo
git remote set-url origin git@github.com:mateoadann/consul_app.git
```

O si preferís HTTPS, configurar credential store:
```bash
git config --global credential.helper store
# El próximo git pull pedirá usuario/token y lo guardará
```
```

**Step 2: Commit**

```bash
git add docs/VPS_SETUP.md
git commit -m "docs: add VPS setup guide for deploy and backups"
```

---

### Task 6: Verificación end-to-end local

**Step 1: Verificar sintaxis de todos los scripts**

Run:
```bash
bash -n scripts/backup-db.sh && bash -n scripts/deploy.sh && echo "OK"
```
Expected: `OK`

**Step 2: Verificar lint**

Run: `flake8 app/ tests/ --max-line-length=120 --exclude=__pycache__,migrations`
Expected: Sin errores

**Step 3: Verificar que el workflow YAML sea válido**

Run:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml')); print('deploy.yml OK')"
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('ci.yml OK')"
```
Expected: Ambos OK

**Step 4: Commit final si hay cambios pendientes y push**

```bash
git push origin dev
```
