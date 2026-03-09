#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
BACKUP_TYPE="${1:?Usage: $0 <auto|manual> [project_dir]}"
PROJECT_DIR="${2:-$(cd "$(dirname "$0")/.." && pwd)}"
BACKUP_BASE="/opt/backups/consul_app"
BACKUP_DIR="${BACKUP_BASE}/${BACKUP_TYPE}"
MAX_BACKUPS=4
TIMESTAMP="$(date +%Y-%m-%d_%H-%M)"
FILENAME="consul_app_${TIMESTAMP}.sql.gz"

# --- Helpers ---
log() { echo "[backup] $*"; }

# --- Validate type ---
if [[ "$BACKUP_TYPE" != "auto" && "$BACKUP_TYPE" != "manual" ]]; then
  log "ERROR: type must be 'auto' or 'manual', got '${BACKUP_TYPE}'"
  exit 1
fi

# --- Read DB credentials from environment / compose defaults ---
DB_USER="${POSTGRES_USER:-consul}"
DB_NAME="${POSTGRES_DB:-consul_app}"

# --- Resolve the db container name ---
DB_CONTAINER="$(docker compose -f "${PROJECT_DIR}/docker-compose.prod.yml" --project-directory "${PROJECT_DIR}" ps -q db)"
if [[ -z "$DB_CONTAINER" ]]; then
  log "ERROR: db container is not running"
  exit 1
fi
log "Found db container: ${DB_CONTAINER:0:12}"

# --- Create backup directory ---
mkdir -p "$BACKUP_DIR"
log "Backup directory: ${BACKUP_DIR}"

# --- Dump & compress ---
log "Starting backup of database '${DB_NAME}' as user '${DB_USER}'..."
TMPFILE="${BACKUP_DIR}/.backup_in_progress.sql"
trap 'rm -f "$TMPFILE" "${BACKUP_DIR}/${FILENAME}"' ERR

docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" > "$TMPFILE"
gzip -c "$TMPFILE" > "${BACKUP_DIR}/${FILENAME}"
rm -f "$TMPFILE"

trap - ERR

# --- Validate backup is not empty ---
FILESIZE="$(stat -f%z "${BACKUP_DIR}/${FILENAME}" 2>/dev/null || stat -c%s "${BACKUP_DIR}/${FILENAME}" 2>/dev/null)"
if [[ "$FILESIZE" -eq 0 ]]; then
  log "ERROR: backup file is empty, removing"
  rm -f "${BACKUP_DIR}/${FILENAME}"
  exit 1
fi
log "Backup created: ${BACKUP_DIR}/${FILENAME} (${FILESIZE} bytes)"

# --- Rotation: keep only MAX_BACKUPS, delete oldest ---
BACKUP_COUNT="$(find "$BACKUP_DIR" -maxdepth 1 -name '*.sql.gz' -type f | wc -l | tr -d ' ')"
if [[ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]]; then
  DELETE_COUNT=$((BACKUP_COUNT - MAX_BACKUPS))
  log "Rotating: removing ${DELETE_COUNT} oldest backup(s) (keeping ${MAX_BACKUPS})"
  find "$BACKUP_DIR" -maxdepth 1 -name '*.sql.gz' -type f -print0 \
    | xargs -0 ls -1t \
    | tail -n "$DELETE_COUNT" \
    | while read -r old; do
        log "Deleting: $(basename "$old")"
        rm -f "$old"
      done
fi

log "Done."
