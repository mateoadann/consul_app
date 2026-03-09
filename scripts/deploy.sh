#!/usr/bin/env bash
set -euo pipefail

# --- Resolve project directory from script location ---
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE=(docker compose -f "${PROJECT_DIR}/docker-compose.prod.yml" --project-directory "${PROJECT_DIR}")

# --- Helpers ---
log() { echo "[deploy] $(date '+%Y-%m-%d %H:%M:%S') $*"; }

log "Starting deploy from ${PROJECT_DIR}"

# --- 1. Pre-deploy backup ---
log "Running pre-deploy backup..."
if "${PROJECT_DIR}/scripts/backup-db.sh" manual "$PROJECT_DIR"; then
  log "Pre-deploy backup completed successfully"
else
  log "WARNING: Pre-deploy backup failed — continuing with deploy"
fi

# --- 2. Pull latest code ---
log "Pulling latest code from origin main..."
git -C "$PROJECT_DIR" pull origin main

# --- 3. Build and start containers ---
log "Building and starting containers..."
"${COMPOSE[@]}" up -d --build

# --- 4. Wait for DB ready (max 60s) ---
log "Waiting for database to be ready..."
TRIES=0
MAX_TRIES=60
until "${COMPOSE[@]}" exec -T db sh -lc 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; do
  TRIES=$((TRIES + 1))
  if [[ "$TRIES" -ge "$MAX_TRIES" ]]; then
    log "ERROR: Database not ready after ${MAX_TRIES}s, aborting"
    exit 1
  fi
  sleep 1
done
log "Database is ready"

# --- 5. Create extensions ---
log "Ensuring PostgreSQL extensions..."
"${COMPOSE[@]}" exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"'
"${COMPOSE[@]}" exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"'

# --- 6. Run database migrations (bootstrap if fresh DB) ---
ALEMBIC_TABLE=$("${COMPOSE[@]}" exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT to_regclass('\''alembic_version'\'')"' | tr -d '[:space:]')
if [[ "$ALEMBIC_TABLE" == "alembic_version" ]]; then
  log "Running database migrations..."
  "${COMPOSE[@]}" exec -T app flask --app wsgi.py db upgrade
else
  log "Fresh database detected: bootstrapping schema + stamp head..."
  "${COMPOSE[@]}" exec -T app python -c 'from app import create_app; from app.extensions import db; import app.models; a=create_app("production"); ctx=a.app_context(); ctx.push(); db.create_all(); ctx.pop()'
  "${COMPOSE[@]}" exec -T app flask --app wsgi.py db stamp head
fi

# --- 7. Ensure admin user exists ---
log "Ensuring admin user..."
"${COMPOSE[@]}" exec -T app flask --app wsgi.py ensure-admin

# --- 8. Clean up dangling images ---
log "Pruning unused Docker images..."
docker image prune -f

log "Deploy completed successfully"
