# AGENTS.md

Guidance for coding agents working in `consul_app`.

## 0) Rules discovery

- Checked for Cursor/Copilot rules in:
  - `.cursorrules`
  - `.cursor/rules/`
  - `.github/copilot-instructions.md`
- Result: none found in this repository.
- Therefore, follow this file plus existing project conventions.

## 1) Project snapshot

- Stack: Flask + SQLAlchemy + Flask-Migrate + Flask-Login + Flask-WTF + Flask-Session.
- DB: PostgreSQL (uses `TSRANGE`, `ExcludeConstraint`, and Postgres extensions).
- Frontend: SSR Jinja templates + HTMX partial updates + small vanilla JS.
- Runtime in Docker dev: app is exposed directly (no nginx required).
- Default dev URL: `http://localhost:5002`.

## 2) Build / run / test commands

Prefer `make` targets when possible.

### Core make targets

- `make help` - list available targets.
- `make env` - create `.env` from `.env.example` if missing.
- `make up` - start Docker stack and bootstrap DB schema (no demo data).
- `make down` - stop Docker stack.
- `make restart` - recreate Docker stack.
- `make logs` - follow Docker logs.
- `make db-bootstrap` - create required extensions and schema only.
- `make seed` - run seed script inside Docker.
- `make shell` - shell into app container.

### Local Python workflow

- `make install` - create `.venv` and install dependencies.
- `make run` - run Flask in debug locally.
- `make seed-local` - run `seed.py` locally.

### Database / migrations

- `make db-init` - init Flask migrations (first time only).
- `make db-migrate msg="your message"` - create migration.
- `make db-upgrade` - apply migrations.

### Tests

- `make test` - run local test suite (verbose: `pytest -vv -rA`).
- `make docker-test` - recreate isolated `consul_app_test` DB and run tests inside Docker (verbose).
- `make docker-test-db` - recreate isolated Docker test DB only.
- `make test-postgres TEST_DATABASE_URL=postgresql+psycopg2://...` - run postgres-marked tests (verbose).

### Run a single test (important)

Local (recommended):

```bash
.venv/bin/pytest tests/test_turnos.py::test_no_overlap_same_consultorio -vv -rA
```

Filter by expression:

```bash
.venv/bin/pytest -k "overlap and consultorio" -vv -rA
```

Single test in Docker:

```bash
docker compose exec app pytest tests/test_turnos.py::test_no_overlap_same_consultorio -vv -rA
```

### Lint / formatting status

- No Ruff/Black/isort/Flake8 config is currently committed.
- Use syntax check as a safety gate:

```bash
python3 -m compileall app tests config.py seed.py wsgi.py
```

- Clean caches:

```bash
make clean-pyc
```

## 3) Architecture and file conventions

- App factory in `app/__init__.py` (`create_app`).
- Extensions in `app/extensions.py`.
- Models in `app/models/`.
- Route handlers in `app/blueprints/<module>/routes.py`.
- Forms in `app/blueprints/<module>/forms.py`.
- Cross-cutting logic in `app/services/` and `app/utils/`.
- Templates:
  - full pages: normal filename, usually extend `base.html`
  - HTMX fragments: prefix with `_`.

## 4) Code style guidelines

### Python formatting

- Use 4 spaces, no tabs.
- Keep lines readable; prefer wrapping long expressions with parentheses.
- Keep functions focused and small when possible.

### Imports

- Group imports in this order:
  1. standard library
  2. third-party
  3. local app imports
- Prefer explicit imports over wildcard imports.
- Keep one logical import per line when practical.

### Naming

- Functions/variables/modules: `snake_case`.
- Classes: `PascalCase`.
- Constants: `UPPER_SNAKE_CASE`.
- Blueprints use `<domain>_bp` (e.g., `turnos_bp`).
- Domain language is Spanish for business entities (`Paciente`, `Profesional`, `Turno`, etc.); keep that consistent.

### Types

- Add type hints on public functions and helpers where practical.
- Use modern union syntax (`str | None`) consistent with existing code.
- Do not over-engineer typing in simple route handlers.

### Data and DB patterns

- Use SQLAlchemy ORM models from `app.models`.
- Use Postgres range types via `psycopg2.extras.DateTimeRange` where turnos are created/updated.
- Preserve exclusion constraints behavior for overlap prevention.
- If handling overlap race conditions, catch `IntegrityError` and check `pgcode == "23P01"`.

### Error handling and UX

- Validate inputs server-side even when HTMX validation exists.
- For form validation failures: re-render template with field errors.
- Use HTTP status intentionally:
  - `422` for invalid form/business validation responses.
  - `409` for conflict-like inline validation where used (e.g., DNI endpoint).
- On DB exceptions during writes: `db.session.rollback()` before returning/raising.
- Use user-friendly flash messages in Spanish tone used in the app.

### Auth, roles, and security

- Protect authenticated views with `@login_required`.
- Protect admin-only sections with `@role_required("admin")`.
- Keep CSRF intact for forms and HTMX requests.
- Do not remove security headers configured in `register_security_headers`.

### Templates and HTMX

- Keep SSR-first flow (no JSON API introduction unless explicitly requested).
- Use HTMX for partial refreshes and lightweight interactions.
- Keep reusable partials in `app/templates/components/` or `_fragment` templates.
- Maintain mobile-first behavior and touch-friendly controls.

### JavaScript and CSS

- JS is minimal and unobtrusive; keep behavior-focused scripts in `app/static/js/app.js`.
- Preserve CSRF header injection for HTMX requests.
- Keep CSS custom (no framework added currently) unless explicitly requested.

## 5) Testing conventions

- Pytest is configured via `tests/conftest.py`.
- `postgres` marker requires `TEST_DATABASE_URL`; otherwise those tests are skipped.
- When adding DB-heavy tests, mark with `@pytest.mark.postgres`.
- Keep tests deterministic and explicit about setup data.

## 6) Practical agent checklist for changes

- Read relevant blueprint, model, template, and service files before editing.
- Keep naming and language consistent with existing Spanish domain terms.
- Update or add tests when behavior changes.
- Run at least a targeted test (single test) for touched behavior.
- Run `compileall` sanity check if no linter is configured.
- Avoid introducing new infra/tools unless requested.
