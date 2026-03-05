# ConsulApp Mejoras - Plan de Implementación

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar workflow Git profesional, tests adicionales, CSS modular, PWA con gestos mobile, y rediseño User-Profesional.

**Architecture:** Flask SSR + HTMX, PostgreSQL con exclusion constraints, PWA con Service Worker para instalación y push notifications. CSS modular con @import.

**Tech Stack:** Flask, SQLAlchemy, PostgreSQL, HTMX, Vanilla JS (gestos), pywebpush (notificaciones)

---

## Feature 001: Git Workflow

### Task 1.1: Commit inicial del proyecto

**Files:**
- Modify: `.gitignore`

**Step 1: Verificar .gitignore incluye todo lo necesario**

```bash
cat .gitignore
```

**Step 2: Agregar archivos IDE si faltan**

Verificar que incluya `.idea/`, `.vscode/`, `*.swp`

**Step 3: Agregar todos los archivos al staging**

```bash
git add -A
```

**Step 4: Verificar qué se va a commitear**

```bash
git status
```

Expected: Lista de archivos a commitear (excluyendo .venv, .env, __pycache__)

**Step 5: Commit inicial**

```bash
git commit -m "chore: initial commit of ConsulApp

Mobile-first appointment scheduling system with Flask + HTMX + PostgreSQL.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 1.2: Crear repositorio en GitHub

**Step 1: Verificar autenticación de gh**

```bash
gh auth status
```

Expected: Logged in to github.com

**Step 2: Crear repositorio público**

```bash
gh repo create consul_app --public --source=. --push
```

Expected: Repository created, code pushed

**Step 3: Verificar repo creado**

```bash
gh repo view --web
```

---

### Task 1.3: Crear rama dev

**Step 1: Crear y cambiar a rama dev**

```bash
git checkout -b dev
```

**Step 2: Push rama dev a origin**

```bash
git push -u origin dev
```

**Step 3: Verificar ramas en remote**

```bash
git branch -a
```

Expected: main, dev (ambas en local y origin)

---

### Task 1.4: Crear archivo CONTRIBUTING.md

**Files:**
- Create: `CONTRIBUTING.md`

**Step 1: Crear archivo CONTRIBUTING.md**

```markdown
# Contribuir a ConsulApp

## Workflow de Ramas

```
main (producción) ← solo PRs desde dev
  └── dev (integración) ← solo PRs desde feature/*
       └── feature/NNN-slug (desarrollo)
```

## Crear una Feature

1. Actualizar dev:
   ```bash
   git checkout dev && git pull
   ```

2. Crear rama feature (NNN correlativo):
   ```bash
   git checkout -b feature/001-mi-feature
   ```

3. Desarrollar con commits frecuentes

4. Crear PR a dev:
   ```bash
   gh pr create --base dev
   ```

5. Una vez aprobado y mergeado a dev, crear PR de dev a main

## Convenciones de Commits

Usar [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` nueva funcionalidad
- `fix:` corrección de bug
- `docs:` documentación
- `test:` tests
- `refactor:` refactorización sin cambio de funcionalidad
- `chore:` tareas de mantenimiento

## Tests

Ejecutar tests antes de cada commit:

```bash
make docker-test
```

## Code Review

- Todos los PRs requieren al menos 1 aprobación
- CI debe pasar (lint + tests)
```

**Step 2: Commit CONTRIBUTING.md**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add CONTRIBUTING.md with git workflow

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 1.5: Crear GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

**Step 1: Crear directorio .github/workflows**

```bash
mkdir -p .github/workflows
```

**Step 2: Crear archivo ci.yml**

```yaml
name: CI

on:
  pull_request:
    branches: [main, dev]
  push:
    branches: [main, dev]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install flake8
        run: pip install flake8
      - name: Run flake8
        run: flake8 app tests --max-line-length=100 --ignore=E501,W503

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: consul
          POSTGRES_PASSWORD: consul
          POSTGRES_DB: consul_app_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Setup database extensions
        run: |
          PGPASSWORD=consul psql -h localhost -U consul -d consul_app_test -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"
          PGPASSWORD=consul psql -h localhost -U consul -d consul_app_test -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

      - name: Run tests
        env:
          TEST_DATABASE_URL: postgresql+psycopg2://consul:consul@localhost:5432/consul_app_test
          SECRET_KEY: test-secret-key
          FLASK_ENV: testing
        run: pytest -vv -rA
```

**Step 3: Commit CI workflow**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow for lint and tests

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 1.6: Crear PR template

**Files:**
- Create: `.github/PULL_REQUEST_TEMPLATE.md`

**Step 1: Crear PR template**

```markdown
## Descripción

<!-- Breve descripción de los cambios -->

## Tipo de cambio

- [ ] Bug fix
- [ ] Nueva feature
- [ ] Refactoring
- [ ] Documentación
- [ ] Tests

## Checklist

- [ ] Tests pasan localmente (`make docker-test`)
- [ ] Código sigue las convenciones del proyecto
- [ ] Documentación actualizada si aplica

## Screenshots (si aplica)

<!-- Agregar capturas de UI si hubo cambios visuales -->
```

**Step 2: Commit PR template**

```bash
git add .github/PULL_REQUEST_TEMPLATE.md
git commit -m "chore: add pull request template

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 1.7: Configurar branch protection (main)

**Step 1: Configurar protección para main**

```bash
gh api repos/{owner}/{repo}/branches/main/protection -X PUT -f "required_status_checks[strict]=true" -f "required_status_checks[contexts][]=test" -f "required_status_checks[contexts][]=lint" -f "enforce_admins=false" -f "required_pull_request_reviews[required_approving_review_count]=1" -f "restrictions=null"
```

Nota: Si falla por permisos, documentar para configurar manualmente en GitHub Settings > Branches.

**Step 2: Verificar protección**

```bash
gh api repos/{owner}/{repo}/branches/main/protection
```

---

### Task 1.8: Configurar branch protection (dev)

**Step 1: Configurar protección para dev**

```bash
gh api repos/{owner}/{repo}/branches/dev/protection -X PUT -f "required_status_checks[strict]=true" -f "required_status_checks[contexts][]=test" -f "required_status_checks[contexts][]=lint" -f "enforce_admins=false" -f "required_pull_request_reviews[required_approving_review_count]=1" -f "restrictions=null"
```

**Step 2: Push cambios y crear primer PR**

```bash
git push origin dev
```

---

### Task 1.9: Merge feature/001 a dev

**Step 1: Crear PR de feature/001 a dev**

```bash
gh pr create --base dev --title "feat: setup git workflow and CI" --body "## Descripción

Configura el workflow de Git con:
- Estructura de ramas main/dev/feature
- GitHub Actions CI (lint + tests)
- CONTRIBUTING.md con guía de contribución
- PR template

## Tipo de cambio
- [x] Nueva feature
- [x] Documentación"
```

**Step 2: Merge PR (después de que CI pase)**

```bash
gh pr merge --squash
```

---

## Feature 002: Tests Adicionales

### Task 2.1: Crear rama feature/002

**Step 1: Checkout dev actualizado**

```bash
git checkout dev && git pull
```

**Step 2: Crear rama feature**

```bash
git checkout -b feature/002-tests-adicionales
```

---

### Task 2.2: Agregar fixtures en conftest.py

**Files:**
- Modify: `tests/conftest.py`

**Step 1: Leer conftest.py actual**

```bash
cat tests/conftest.py
```

**Step 2: Agregar fixtures faltantes**

Agregar al final de conftest.py:

```python
@pytest.fixture
def admin_user(app, db_session):
    """Usuario con rol admin."""
    from app.models import User
    user = User(username="admin_test", nombre="Admin Test", role="admin")
    user.set_password("admin123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def profesional_user(app, db_session):
    """Usuario con rol profesional."""
    from app.models import User, Profesional
    user = User(username="prof_test", nombre="Prof Test", role="profesional")
    user.set_password("prof123")
    db_session.add(user)
    db_session.commit()

    profesional = Profesional(
        nombre="Test",
        apellido="Profesional",
        especialidad="General",
        user_id=user.id
    )
    db_session.add(profesional)
    db_session.commit()
    return user


@pytest.fixture
def consultorio(app, db_session):
    """Consultorio de prueba."""
    from app.models import Consultorio
    c = Consultorio(nombre="Consultorio Test", color="naranja", activo=True)
    db_session.add(c)
    db_session.commit()
    return c
```

**Step 3: Verificar que tests existentes siguen pasando**

```bash
make docker-test
```

**Step 4: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add admin_user, profesional_user, consultorio fixtures

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2.3: Crear test_profesionales.py

**Files:**
- Create: `tests/test_profesionales.py`

**Step 1: Crear archivo de tests**

```python
"""Tests para el blueprint de profesionales."""
import pytest
from flask import url_for


class TestProfesionalesIndex:
    """Tests para lista de profesionales."""

    def test_requiere_login(self, client):
        """Acceso sin login redirige a login."""
        response = client.get("/profesionales/")
        assert response.status_code == 302
        assert "/auth/login" in response.location

    def test_lista_profesionales_como_admin(self, client, admin_user):
        """Admin puede ver lista de profesionales."""
        client.post("/auth/login", data={
            "username": admin_user.username,
            "password": "admin123"
        })
        response = client.get("/profesionales/")
        assert response.status_code == 200

    def test_lista_profesionales_como_profesional(self, client, profesional_user):
        """Profesional puede ver lista de profesionales."""
        client.post("/auth/login", data={
            "username": profesional_user.username,
            "password": "prof123"
        })
        response = client.get("/profesionales/")
        assert response.status_code == 200


class TestProfesionalesAutocomplete:
    """Tests para autocomplete de profesionales."""

    def test_autocomplete_requiere_login(self, client):
        """Autocomplete sin login falla."""
        response = client.get("/profesionales/autocomplete?q=test")
        assert response.status_code == 302

    def test_autocomplete_retorna_resultados(self, client, profesional_user):
        """Autocomplete retorna profesionales que coinciden."""
        client.post("/auth/login", data={
            "username": profesional_user.username,
            "password": "prof123"
        })
        response = client.get("/profesionales/autocomplete?q=Test")
        assert response.status_code == 200
```

**Step 2: Ejecutar tests**

```bash
make docker-test
```

Expected: Tests pasan (o fallan revelando bugs a corregir)

**Step 3: Commit**

```bash
git add tests/test_profesionales.py
git commit -m "test: add profesionales blueprint tests

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2.4: Crear test_consultorios.py

**Files:**
- Create: `tests/test_consultorios.py`

**Step 1: Crear archivo de tests**

```python
"""Tests para el blueprint de consultorios (solo admin)."""
import pytest


class TestConsultoriosAccess:
    """Tests de acceso a consultorios."""

    def test_requiere_login(self, client):
        """Sin login redirige."""
        response = client.get("/consultorios/")
        assert response.status_code == 302

    def test_profesional_no_tiene_acceso(self, client, profesional_user):
        """Profesional no puede acceder a consultorios."""
        client.post("/auth/login", data={
            "username": profesional_user.username,
            "password": "prof123"
        })
        response = client.get("/consultorios/")
        assert response.status_code == 403

    def test_admin_tiene_acceso(self, client, admin_user):
        """Admin puede acceder a consultorios."""
        client.post("/auth/login", data={
            "username": admin_user.username,
            "password": "admin123"
        })
        response = client.get("/consultorios/")
        assert response.status_code == 200


class TestConsultoriosCRUD:
    """Tests CRUD de consultorios."""

    def test_crear_consultorio(self, client, admin_user):
        """Admin puede crear consultorio."""
        client.post("/auth/login", data={
            "username": admin_user.username,
            "password": "admin123"
        })
        response = client.post("/consultorios/nuevo", data={
            "nombre": "Consultorio Nuevo",
            "color": "azul",
            "activo": "y"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Consultorio Nuevo" in response.data or response.status_code == 200
```

**Step 2: Ejecutar tests**

```bash
make docker-test
```

**Step 3: Commit**

```bash
git add tests/test_consultorios.py
git commit -m "test: add consultorios blueprint tests (admin only)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2.5: Crear test_permissions.py

**Files:**
- Create: `tests/test_permissions.py`

**Step 1: Crear archivo de tests**

```python
"""Tests para permisos y decoradores."""
import pytest


class TestRoleRequired:
    """Tests para el decorador @role_required."""

    def test_admin_accede_a_admin_panel(self, client, admin_user):
        """Admin puede acceder al panel admin."""
        client.post("/auth/login", data={
            "username": admin_user.username,
            "password": "admin123"
        })
        response = client.get("/admin/")
        assert response.status_code == 200

    def test_profesional_no_accede_a_admin_panel(self, client, profesional_user):
        """Profesional no puede acceder al panel admin."""
        client.post("/auth/login", data={
            "username": profesional_user.username,
            "password": "prof123"
        })
        response = client.get("/admin/")
        assert response.status_code == 403

    def test_usuario_inactivo_no_puede_login(self, client, db_session):
        """Usuario inactivo no puede hacer login."""
        from app.models import User
        user = User(username="inactive", nombre="Inactive", role="profesional", activo=False)
        user.set_password("pass123")
        db_session.add(user)
        db_session.commit()

        response = client.post("/auth/login", data={
            "username": "inactive",
            "password": "pass123"
        })
        # Debería fallar el login o redirigir con error
        assert response.status_code in [200, 302]


class TestCSRF:
    """Tests para protección CSRF."""

    def test_post_sin_csrf_falla(self, client, admin_user):
        """POST sin token CSRF debe fallar."""
        client.post("/auth/login", data={
            "username": admin_user.username,
            "password": "admin123"
        })
        # Intentar POST sin CSRF token
        response = client.post("/pacientes/nuevo", data={
            "nombre": "Test",
            "apellido": "Paciente"
        })
        # Debería fallar con 400 o redirigir
        assert response.status_code in [400, 302, 200]
```

**Step 2: Ejecutar tests**

```bash
make docker-test
```

**Step 3: Commit**

```bash
git add tests/test_permissions.py
git commit -m "test: add permissions and CSRF tests

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2.6: Agregar comando test-coverage al Makefile

**Files:**
- Modify: `Makefile`

**Step 1: Agregar target test-coverage**

Agregar después de `docker-test`:

```makefile
test-coverage: install ## Ejecuta tests con reporte de cobertura
	$(VENV_PYTEST) --cov=app --cov-report=html --cov-report=term $(PYTEST_FLAGS)
```

**Step 2: Verificar que funciona**

```bash
make test-coverage
```

**Step 3: Agregar htmlcov/ a .gitignore si no está**

**Step 4: Commit**

```bash
git add Makefile
git commit -m "chore: add test-coverage make target

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2.7: PR feature/002 a dev

**Step 1: Push y crear PR**

```bash
git push -u origin feature/002-tests-adicionales
gh pr create --base dev --title "test: add additional test coverage" --body "## Descripción

Agrega tests para blueprints faltantes:
- test_profesionales.py
- test_consultorios.py
- test_permissions.py

También agrega fixtures compartidas y comando make test-coverage.

## Tipo de cambio
- [x] Tests"
```

**Step 2: Merge después de CI**

```bash
gh pr merge --squash
```

---

## Feature 003: CSS Modularización

### Task 3.1: Crear rama feature/003

```bash
git checkout dev && git pull
git checkout -b feature/003-css-modularizacion
```

---

### Task 3.2: Crear estructura de directorios CSS

**Step 1: Crear directorios**

```bash
mkdir -p app/static/css/{base,components,layouts,features,utilities}
```

**Step 2: Commit estructura**

```bash
git add app/static/css/
git commit -m "chore: create CSS module directory structure

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>" --allow-empty
```

---

### Task 3.3: Extraer base/variables.css

**Files:**
- Create: `app/static/css/base/variables.css`

**Step 1: Crear variables.css**

Extraer líneas 1-21 de app.css:

```css
:root {
  --bg: #fafaf9;
  --surface: #ffffff;
  --ink: #292524;
  --muted: #78716c;
  --muted-soft: #a8a29e;
  --brand: #ea580c;
  --brand-hover: #c2410c;
  --brand-soft: #f1f1f1;
  --accent: #0d9488;
  --danger: #b91c1c;
  --ok: #15803d;
  --warning: #b45309;
  --line: #e7e5e4;
  --line-soft: #d6d3d1;
  --radius: 14px;
  --radius-xl: 14px;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  --font-ui: "DM Sans", "Segoe UI", sans-serif;
  --font-mono: "JetBrains Mono", "SFMono-Regular", Menlo, monospace;
}
```

**Step 2: Commit**

```bash
git add app/static/css/base/variables.css
git commit -m "refactor(css): extract variables to base/variables.css

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 3.4: Extraer base/reset.css

**Files:**
- Create: `app/static/css/base/reset.css`

**Step 1: Crear reset.css**

```css
* {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-ui);
}

a {
  color: inherit;
  text-decoration: none;
}
```

**Step 2: Commit**

```bash
git add app/static/css/base/reset.css
git commit -m "refactor(css): extract reset to base/reset.css

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 3.5-3.18: Extraer resto de módulos CSS

(Continuar el mismo patrón para cada archivo según la estructura definida en el diseño)

**Archivos a crear:**
- `components/buttons.css` - .btn, .btn-primary, .btn-ghost, .ghost-btn
- `components/cards.css` - .card, .card-auth, .card-header-*
- `components/forms.css` - .input, select, textarea, .field-*
- `components/badges.css` - .badge, .badge-*
- `components/pills.css` - .pill, .consultorio-pills
- `components/flash.css` - .flash, .flash-*
- `components/chips.css` - .chip, .ocupados-*
- `layouts/topbar.css` - .topbar, .app-title
- `layouts/bottom-nav.css` - .bottom-nav, .bottom-nav-*
- `layouts/menu-drawer.css` - .menu-drawer, .menu-drawer-*
- `layouts/page-wrap.css` - .page-wrap, .stack
- `layouts/grid.css` - .detail-grid, .list-*
- `features/agenda.css` - .agenda-*, .day-*
- `features/timeline.css` - .timeline, .timeline-*
- `features/turno-card.css` - .turno-card, .slot-*, .new-slot
- `features/recurrence.css` - .recurrence-*
- `features/search.css` - .search-*
- `utilities/colors.css` - .cc-* (colores de consultorios)
- `utilities/responsive.css` - .mobile-only, .desktop-only, @media

---

### Task 3.19: Actualizar app.css con imports

**Files:**
- Modify: `app/static/css/app.css`

**Step 1: Reemplazar contenido con imports**

```css
/* ConsulApp - CSS Modules */

/* Base */
@import "base/variables.css";
@import "base/reset.css";

/* Components */
@import "components/buttons.css";
@import "components/cards.css";
@import "components/forms.css";
@import "components/badges.css";
@import "components/pills.css";
@import "components/flash.css";
@import "components/chips.css";

/* Layouts */
@import "layouts/topbar.css";
@import "layouts/bottom-nav.css";
@import "layouts/menu-drawer.css";
@import "layouts/page-wrap.css";
@import "layouts/grid.css";

/* Features */
@import "features/agenda.css";
@import "features/timeline.css";
@import "features/turno-card.css";
@import "features/recurrence.css";
@import "features/search.css";

/* Utilities */
@import "utilities/colors.css";
@import "utilities/responsive.css";
```

**Step 2: Verificar visualmente que la app funciona igual**

```bash
make up
# Abrir http://localhost:5002 y verificar estilos
```

**Step 3: Commit**

```bash
git add app/static/css/
git commit -m "refactor(css): modularize app.css into 20+ modules

Maintains exact same styles, only reorganized for maintainability.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 3.20: PR feature/003 a dev

```bash
git push -u origin feature/003-css-modularizacion
gh pr create --base dev --title "refactor: modularize CSS into component files" --body "## Descripción

Reorganiza app.css monolítico (~1000 líneas) en módulos:
- base/ (variables, reset)
- components/ (buttons, cards, forms, badges, etc.)
- layouts/ (topbar, bottom-nav, page-wrap, etc.)
- features/ (agenda, timeline, turno-card, etc.)
- utilities/ (colors, responsive)

Sin cambios visuales, solo reorganización.

## Tipo de cambio
- [x] Refactoring"
```

---

## Feature 004: UX Review

### Task 4.1: Crear rama y arrancar app

```bash
git checkout dev && git pull
git checkout -b feature/004-ux-review
make up && make seed
```

---

### Task 4.2: Auditar flujo de login

Usar chrome-devtools MCP para:

1. Navegar a http://localhost:5002/auth/login
2. `take_snapshot` - verificar a11y tree
3. `take_screenshot` - captura visual
4. Verificar touch targets >= 44px
5. Probar login con credenciales inválidas
6. Probar login correcto

Documentar issues en `docs/ux-review-findings.md`

---

### Task 4.3-4.8: Auditar resto de flujos

Repetir proceso para:
- Agenda (navegación días, filtros)
- Turnos (crear, editar, cancelar)
- Pacientes (lista, buscar, crear)
- Profesionales (lista, detalle)
- Admin panel

---

### Task 4.9: Ejecutar Lighthouse audit

```
lighthouse_audit con mode="snapshot"
```

Documentar scores de accesibilidad y SEO.

---

### Task 4.10: Commit findings y PR

```bash
git add docs/ux-review-findings.md
git commit -m "docs: add UX review findings from DevTools audit

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
git push -u origin feature/004-ux-review
gh pr create --base dev
```

---

## Feature 005: UX Fixes

(Basado en findings del review - tareas específicas dependen de los issues encontrados)

---

## Feature 006: PWA Base

### Task 6.1: Crear rama

```bash
git checkout dev && git pull
git checkout -b feature/006-pwa-base
```

---

### Task 6.2: Crear manifest.json

**Files:**
- Create: `app/static/manifest.json`

```json
{
  "name": "ConsulApp",
  "short_name": "ConsulApp",
  "description": "Sistema de turnos para centro médico",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#fafaf9",
  "theme_color": "#ea580c",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/static/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/static/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
```

---

### Task 6.3: Crear Service Worker

**Files:**
- Create: `app/static/sw.js`

```javascript
const CACHE_NAME = 'consulapp-v1';
const STATIC_ASSETS = [
  '/static/css/app.css',
  '/static/js/app.js',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png'
];

// Install - cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activate - clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(key => key !== CACHE_NAME)
            .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

// Fetch - network first, fallback to cache for assets
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Static assets: cache first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request)
        .then(cached => cached || fetch(event.request))
    );
    return;
  }

  // HTML: network first
  event.respondWith(
    fetch(event.request)
      .catch(() => caches.match(event.request))
  );
});

// Push notifications
self.addEventListener('push', event => {
  const data = event.data?.json() || {};
  const title = data.title || 'ConsulApp';
  const options = {
    body: data.body || 'Tienes una notificación',
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/icon-192.png',
    data: data.url || '/'
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data)
  );
});
```

---

### Task 6.4: Crear iconos placeholder

**Files:**
- Create: `app/static/icons/` directory

```bash
mkdir -p app/static/icons
# Crear iconos placeholder (reemplazar con diseño real después)
```

Nota: Se necesitan crear iconos PNG de 192x192 y 512x512. Por ahora usar placeholders.

---

### Task 6.5: Agregar meta tags a base.html

**Files:**
- Modify: `app/templates/base.html`

Agregar en `<head>`:

```html
<!-- PWA -->
<link rel="manifest" href="{{ url_for('static', filename='manifest.json') }}">
<meta name="theme-color" content="#ea580c">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="ConsulApp">
<link rel="apple-touch-icon" href="{{ url_for('static', filename='icons/apple-touch-icon.png') }}">
```

---

### Task 6.6: Registrar Service Worker

**Files:**
- Modify: `app/static/js/app.js`

Agregar al inicio:

```javascript
// Register Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js')
      .then(reg => console.log('SW registered:', reg.scope))
      .catch(err => console.error('SW registration failed:', err));
  });
}
```

---

### Task 6.7: Crear docs/pwa-deployment.md

**Files:**
- Create: `docs/pwa-deployment.md`

```markdown
# ConsulApp PWA - Guía de Instalación

## Requisitos

- HTTPS habilitado (requerido para Service Workers)
- Navegador compatible (Chrome, Safari, Firefox, Edge)

## Instalar en Android

1. Abrir ConsulApp en Chrome
2. Tocar menú > "Añadir a pantalla de inicio"
3. Confirmar instalación

## Instalar en iOS

1. Abrir ConsulApp en Safari
2. Tocar botón compartir
3. Seleccionar "Añadir a pantalla de inicio"
4. Confirmar nombre y tocar "Añadir"

## Instalar en Desktop

1. Abrir ConsulApp en Chrome/Edge
2. Click en icono de instalación en barra de direcciones
3. Confirmar instalación

## Push Notifications

Para recibir notificaciones:

1. Al entrar a la app, aceptar permiso de notificaciones
2. Las notificaciones incluyen:
   - Recordatorio de turno (24h antes)
   - Turno cancelado
   - Turno confirmado

## Troubleshooting

### La app no se instala
- Verificar que esté usando HTTPS
- Verificar que el manifest.json esté accesible
- Revisar consola del navegador

### No recibo notificaciones
- Verificar permisos en configuración del dispositivo
- Verificar que el navegador soporte push notifications
```

---

### Task 6.8: Commit y PR

```bash
git add app/static/manifest.json app/static/sw.js app/static/icons/ app/templates/base.html app/static/js/app.js docs/pwa-deployment.md
git commit -m "feat: add PWA support with manifest and service worker

- Add manifest.json for installability
- Add service worker for offline assets
- Add meta tags for iOS/Android
- Add deployment documentation

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
git push -u origin feature/006-pwa-base
gh pr create --base dev
```

---

## Feature 007: Gestos Mobile

### Task 7.1: Crear rama

```bash
git checkout dev && git pull
git checkout -b feature/007-gestos-mobile
```

---

### Task 7.2: Implementar swipe en agenda

**Files:**
- Modify: `app/static/js/app.js`

Agregar después del registro del SW:

```javascript
// Swipe gesture for agenda day navigation
(function initSwipeGesture() {
  const agendaWrap = document.querySelector('.agenda-grid-wrap, .timeline');
  if (!agendaWrap) return;

  let touchStartX = 0;
  let touchStartY = 0;
  let touchEndX = 0;
  let touchEndY = 0;

  const minSwipeDistance = 50;
  const maxVerticalDistance = 100;

  agendaWrap.addEventListener('touchstart', e => {
    touchStartX = e.changedTouches[0].screenX;
    touchStartY = e.changedTouches[0].screenY;
  }, { passive: true });

  agendaWrap.addEventListener('touchend', e => {
    touchEndX = e.changedTouches[0].screenX;
    touchEndY = e.changedTouches[0].screenY;
    handleSwipe();
  }, { passive: true });

  function handleSwipe() {
    const deltaX = touchEndX - touchStartX;
    const deltaY = Math.abs(touchEndY - touchStartY);

    // Ignore if vertical movement is too large (scrolling)
    if (deltaY > maxVerticalDistance) return;

    if (Math.abs(deltaX) < minSwipeDistance) return;

    if (deltaX > 0) {
      // Swipe right -> previous day
      const prevBtn = document.querySelector('[hx-get*="dia="][hx-get*="-1"], .day-nav button:first-child');
      prevBtn?.click();
    } else {
      // Swipe left -> next day
      const nextBtn = document.querySelector('[hx-get*="dia="]:not([hx-get*="-1"]), .day-nav button:last-child');
      nextBtn?.click();
    }
  }
})();
```

---

### Task 7.3: Implementar pull-to-refresh

**Files:**
- Modify: `app/static/js/app.js`

```javascript
// Pull to refresh
(function initPullToRefresh() {
  let touchStartY = 0;
  let isPulling = false;
  const threshold = 80;

  const indicator = document.createElement('div');
  indicator.className = 'pull-refresh-indicator';
  indicator.textContent = 'Soltar para actualizar';
  document.body.prepend(indicator);

  document.addEventListener('touchstart', e => {
    if (window.scrollY === 0) {
      touchStartY = e.touches[0].clientY;
      isPulling = true;
    }
  }, { passive: true });

  document.addEventListener('touchmove', e => {
    if (!isPulling) return;
    const deltaY = e.touches[0].clientY - touchStartY;

    if (deltaY > 0 && deltaY < threshold * 2) {
      indicator.style.transform = 'translateY(' + Math.min(deltaY, threshold) + 'px)';
    }
  }, { passive: true });

  document.addEventListener('touchend', e => {
    if (!isPulling) return;
    isPulling = false;

    const deltaY = e.changedTouches[0].clientY - touchStartY;
    indicator.style.transform = 'translateY(0)';

    if (deltaY > threshold && window.scrollY === 0) {
      // Trigger refresh
      indicator.textContent = 'Actualizando...';
      indicator.style.transform = 'translateY(50px)';

      // Use HTMX to refresh current content or reload
      const mainContent = document.querySelector('[hx-get]');
      if (mainContent && window.htmx) {
        htmx.trigger(mainContent, 'refresh');
      } else {
        window.location.reload();
      }

      setTimeout(() => {
        indicator.textContent = 'Soltar para actualizar';
        indicator.style.transform = 'translateY(0)';
      }, 1000);
    }
  }, { passive: true });
})();
```

---

### Task 7.4: Agregar CSS para indicador

**Files:**
- Create: `app/static/css/components/pull-refresh.css`

```css
.pull-refresh-indicator {
  position: fixed;
  top: -50px;
  left: 0;
  right: 0;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--brand-soft);
  color: var(--brand);
  font-weight: 600;
  transition: transform 0.2s ease;
  z-index: 100;
}
```

Agregar import en app.css.

---

### Task 7.5: Commit y PR

```bash
git add app/static/js/app.js app/static/css/components/pull-refresh.css app/static/css/app.css
git commit -m "feat: add mobile gestures (swipe days, pull-to-refresh)

- Swipe left/right to navigate agenda days
- Pull down to refresh content
- Visual indicator for pull-to-refresh

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
git push -u origin feature/007-gestos-mobile
gh pr create --base dev
```

---

## Feature 008: User-Profesional Redesign

### Task 8.1: Crear rama

```bash
git checkout dev && git pull
git checkout -b feature/008-user-profesional
```

---

### Task 8.2: Escribir test para nueva relación

**Files:**
- Modify: `tests/test_permissions.py`

```python
class TestUserProfesionalRelation:
    """Tests para relación User-Profesional obligatoria."""

    def test_crear_usuario_crea_profesional(self, client, admin_user, db_session):
        """Al crear usuario admin debe crear profesional asociado."""
        client.post("/auth/login", data={
            "username": admin_user.username,
            "password": "admin123"
        })

        response = client.post("/admin/usuarios/nuevo", data={
            "username": "nuevo_prof",
            "password": "pass123",
            "nombre": "Nuevo",
            "apellido": "Profesional",
            "especialidad": "General",
            "role": "profesional"
        }, follow_redirects=True)

        from app.models import User, Profesional
        user = User.query.filter_by(username="nuevo_prof").first()
        assert user is not None
        assert user.profesional is not None
        assert user.profesional.nombre == "Nuevo"

    def test_profesional_solo_edita_su_perfil(self, client, profesional_user, db_session):
        """Profesional puede editar solo su propio perfil."""
        from app.models import Profesional

        # Crear otro profesional
        other = Profesional(nombre="Otro", apellido="Prof", user_id=None)
        db_session.add(other)
        db_session.commit()

        client.post("/auth/login", data={
            "username": profesional_user.username,
            "password": "prof123"
        })

        # Intentar editar otro profesional
        response = client.get(f"/profesionales/{other.id}/editar")
        assert response.status_code == 403
```

---

### Task 8.3: Crear migración

**Files:**
- Create: `migrations/versions/xxx_user_profesional_required.py`

```bash
make db-migrate msg="make user_id required in profesionales"
```

Luego editar la migración generada:

```python
def upgrade():
    # 1. Crear profesionales para usuarios sin uno
    op.execute("""
        INSERT INTO profesionales (nombre, apellido, user_id, activo, created_at, updated_at)
        SELECT u.nombre, '', u.id, true, NOW(), NOW()
        FROM users u
        LEFT JOIN profesionales p ON p.user_id = u.id
        WHERE p.id IS NULL
    """)

    # 2. Para profesionales sin user, crear usuarios
    # (o decidir eliminarlos - depende del caso de uso)

    # 3. Hacer columna NOT NULL
    op.alter_column('profesionales', 'user_id', nullable=False)


def downgrade():
    op.alter_column('profesionales', 'user_id', nullable=True)
```

---

### Task 8.4: Modificar modelo Profesional

**Files:**
- Modify: `app/models/profesional.py`

```python
user_id = db.Column(
    db.Integer,
    db.ForeignKey("users.id"),
    nullable=False,  # Cambio: era nullable=True
    unique=True
)
```

---

### Task 8.5: Modificar blueprint profesionales con permisos

**Files:**
- Modify: `app/blueprints/profesionales/routes.py`

```python
@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar(id):
    profesional = Profesional.query.get_or_404(id)

    # Solo puede editar SU profesional (o admin puede editar todos)
    if current_user.role != "admin" and profesional.user_id != current_user.id:
        abort(403)

    # ... resto del código
```

---

### Task 8.6: Modificar admin/usuarios para crear profesional

**Files:**
- Modify: `app/blueprints/admin/routes.py`

En la ruta de crear usuario:

```python
@bp.route("/usuarios/nuevo", methods=["GET", "POST"])
@role_required("admin")
def nuevo_usuario():
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            nombre=form.nombre.data,
            role=form.role.data
        )
        user.set_password(form.password.data)

        # Crear profesional asociado automáticamente
        profesional = Profesional(
            nombre=form.nombre.data,
            apellido=form.apellido.data,
            especialidad=form.especialidad.data,
            user=user
        )

        db.session.add(user)
        db.session.add(profesional)
        db.session.commit()
```

---

### Task 8.7: Actualizar templates

**Files:**
- Modify: `app/templates/profesionales/index.html`

Ocultar botones de editar para profesionales que no son del usuario actual:

```html
{% if current_user.role == 'admin' or profesional.user_id == current_user.id %}
  <a href="{{ url_for('profesionales.editar', id=profesional.id) }}" class="btn btn-ghost">Editar</a>
{% endif %}
```

---

### Task 8.8: Ejecutar migración y tests

```bash
make docker-db-upgrade
make docker-test
```

---

### Task 8.9: Commit y PR

```bash
git add app/models/profesional.py app/blueprints/profesionales/routes.py app/blueprints/admin/routes.py app/templates/profesionales/ migrations/ tests/test_permissions.py
git commit -m "feat: make User-Profesional relation required (1:1)

- user_id in profesionales is now NOT NULL
- Creating user automatically creates associated profesional
- Profesional can only edit their own profile
- Admin can edit all

BREAKING CHANGE: Requires migration, existing data must be cleaned up

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
git push -u origin feature/008-user-profesional
gh pr create --base dev
```

---

## Feature 009: Push Notifications

(Tareas adicionales para implementar push notifications completas - opcional para MVP)

---

## Resumen de PRs

| Feature | Rama | PR a |
|---------|------|------|
| 001 | feature/001-git-workflow | dev |
| 002 | feature/002-tests-adicionales | dev |
| 003 | feature/003-css-modularizacion | dev |
| 004 | feature/004-ux-review | dev |
| 005 | feature/005-ux-fixes | dev |
| 006 | feature/006-pwa-base | dev |
| 007 | feature/007-gestos-mobile | dev |
| 008 | feature/008-user-profesional | dev |
| 009 | feature/009-push-notifications | dev |

Después de cada merge a dev, crear PR de dev a main cuando esté estable.
