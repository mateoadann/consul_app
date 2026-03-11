# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ConsulApp is a mobile-first appointment scheduling system for a medical center. Professionals (doctors, therapists) manage their own appointments from their phones — there is no receptionist role. Any professional can view all offices/schedules and book appointments for themselves or colleagues.

Two roles only: `admin` (configures offices, professionals, users) and `profesional` (books/manages appointments).

## Commands

```bash
# Docker (primary workflow)
make env             # create .env from .env.example (first time)
make up              # build + start stack + bootstrap schema (postgres, redis, app on port 5002)
make seed            # optional: load sample data (admin/admin123, 3 professionals, 5 patients)
make logs            # tail logs
make down            # stop stack
make shell           # sh into app container
make help            # list all available make targets

# Database migrations
make db-migrate msg="description"   # generate migration
make db-upgrade                      # apply migrations

# Tests (require Postgres — SQLite cannot run tsrange/btree_gist)
export TEST_DATABASE_URL=postgresql+psycopg2://consul:consul@localhost:5432/consul_app_test
pytest -vv -rA            # all tests (verbose)
pytest tests/test_turnos.py -k test_solapamiento -vv -rA   # single test
make docker-test          # recreate consul_app_test + run tests in container (verbose)

# Local dev (without Docker)
make install         # creates .venv and installs deps
make run             # flask run --debug

# Production
make prod-up         # build + start production stack (Nginx + app + db)
make prod-db-upgrade # apply migrations in production
make prod-logs       # tail production logs
```

## Architecture

**Flask SSR + HTMX** — no SPA, no JSON APIs. Full pages on first load, HTMX partial fragments for interactions (day switching, autocomplete, state changes). Templates prefixed with `_` (e.g., `_grilla.html`) are HTMX fragments that do NOT extend `base.html`.

### Key paths

- `app/__init__.py` — `create_app()` factory; registers blueprints, security headers, error handlers, audit hooks
- `app/extensions.py` — SQLAlchemy, Migrate, LoginManager, CSRFProtect, Session instances
- `app/models/turno.py` — Central model. Uses `TSRANGE` column + 3 PostgreSQL `ExcludeConstraint`s (via `btree_gist`) to prevent overlapping appointments per office, per professional, and per patient. State machine with `TRANSICIONES_VALIDAS` dict and `apply_state()` method
- `app/models/audit.py` — `register_turno_audit_listeners()` hooks into SQLAlchemy `after_insert`/`after_update` events. Audit metadata (user_id, IP) flows via `db.session.info` set in `before_request` hook
- `app/services/disponibilidad.py` — Day grid builder, conflict detection (`find_conflicts`), alternative slot suggestions (`suggest_alternatives`)
- `app/utils/decorators.py` — `@role_required(*roles)` and `htmx_request()` helper
- `app/utils/helpers.py` — `daterange_slots()` generates 15-min time slots (08:00–20:00), `parse_iso_date()`, `is_15_minute_increment()`

### Blueprints

| Blueprint | Prefix | Access |
|-----------|--------|--------|
| `auth` | `/auth` | Public |
| `agenda` | `/` | Authenticated |
| `turnos` | `/turnos` | Authenticated |
| `pacientes` | `/pacientes` | Authenticated |
| `profesionales` | `/profesionales` | Admin (except autocomplete) |
| `consultorios` | `/consultorios` | Admin |
| `admin` | `/admin` | Admin |

### Anti-overlap strategy

Two layers: (1) Application-level `find_conflicts()` check before insert for friendly UX messages, (2) PostgreSQL exclusion constraints as absolute guarantee. Catch `sqlalchemy.exc.IntegrityError` with pgcode `23P01` for race conditions between concurrent users.

## Domain Rules

- Appointment states: `reservado → confirmado → atendido` and `reservado/confirmado → cancelado`. Terminal states: `atendido`, `cancelado`.
- Duration: min 15 min, max 120 min (enforced by DB CHECK constraint)
- Time slots are 15-minute increments
- Cancelled appointments don't block scheduling (exclusion constraints use `WHERE estado != 'cancelado'`)
- `created_by` tracks who booked (may differ from the assigned professional)

### Recurring appointments (series)

- When creating a new appointment, enable "Repetir turno" to create a series
- Multiple patterns per week: day + start/end time + office
- Configure repeat interval (every N weeks) and end date
- Series are processed in partial mode: creates available slots, logs failures
- `TurnoSerieLog` tracks series metadata and failure details (`fallidos_json`)

## CSRF with HTMX

CSRF token is sent via `X-CSRFToken` header, configured globally in `app.js` through `htmx:configRequest` event. The meta tag `csrf-token` in `base.html` provides the value.

## Git Workflow

Three branch types with strict rules:

### Branches

| Branch | Purpose | Receives PRs from | Direct push |
|--------|---------|-------------------|-------------|
| `main` | Production | `dev` only | **NEVER** |
| `dev` | Development/integration | `feature/*` only | **NEVER** |
| `feature/NNN-slug` | All changes happen here | — | Yes |

### Rules (MANDATORY)

1. **Before ANY change**: verify you are on the correct `feature/NNN-slug` branch. If not, create or switch to one.
2. **Never commit directly to `main` or `dev`**. All work goes through feature branches.
3. **Feature branch naming**: `feature/NNN-slug` where NNN is a zero-padded sequential number (e.g., `feature/009-new-feature`).
4. **Before commit & push**: run ALL backend tests (`make docker-test`) and any relevant frontend tests (Chrome DevTools). Then wait for user confirmation before committing and pushing.
5. **Merge path**: `feature/* → PR to dev → PR to main`. No skipping steps.
6. **Creating a new feature branch**: always branch from `dev` (`git checkout dev && git pull && git checkout -b feature/NNN-slug`).

### Pre-commit checklist

- [ ] On correct feature branch
- [ ] Backend tests pass (`make docker-test`)
- [ ] Frontend tested (if applicable, via Chrome DevTools)
- [ ] User confirmed commit & push

## Database Requirements

PostgreSQL 16+ with extensions `btree_gist` and `pg_trgm` (created by `init-db.sql` and `seed.py`). Trigram indexes on `pacientes` and `profesionales` name fields are created in `seed.py`, not in migrations.
