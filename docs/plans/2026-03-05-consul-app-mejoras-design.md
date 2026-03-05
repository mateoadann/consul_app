# ConsulApp - Diseño de Mejoras

**Fecha:** 2026-03-05
**Estado:** Aprobado

## Resumen Ejecutivo

Plan de mejoras para ConsulApp que incluye: establecer workflow de Git profesional, agregar tests, modularizar CSS, auditar UX/UI, implementar PWA con gestos mobile, y rediseñar la relación User-Profesional.

## Decisiones Tomadas

| Aspecto | Decisión |
|---------|----------|
| Repositorio | Crear nuevo repo público en GitHub |
| Registro usuarios | Solo admin crea usuarios |
| PWA scope | Add to Home Screen + Push notifications |
| Gestos mobile | Swipe horizontal + Pull-to-refresh |
| Orden de trabajo | Lógico (Git → Tests → CSS → UX → PWA → User-Profesional) |

---

## 1. Git Workflow

### Estructura de Ramas
```
main (producción)
  └── dev (integración)
       └── feature/001-git-workflow
       └── feature/002-tests-adicionales
       └── ...
```

### Reglas de Protección
- **main**: Solo recibe PRs desde dev, requiere status checks
- **dev**: Solo recibe PRs desde feature/*, requiere status checks
- **feature/NNN-slug**: Trabajo activo, numeración correlativa

### CI Pipeline (.github/workflows/ci.yml)
- Trigger: PR a main o dev
- Jobs: lint (flake8), test (pytest con postgres)

### Archivos a Crear
- `.gitignore`
- `CONTRIBUTING.md`
- `.github/workflows/ci.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`

---

## 2. Tests Adicionales

### Tests Nuevos
| Archivo | Cobertura |
|---------|-----------|
| `test_profesionales.py` | CRUD profesionales, autocomplete |
| `test_consultorios.py` | CRUD consultorios (solo admin) |
| `test_admin.py` | Panel admin, gestión usuarios |
| `test_permissions.py` | Decorador @role_required, permisos |

### Fixtures a Agregar (conftest.py)
- `admin_user`
- `profesional_user`
- `consultorio`
- `profesional`

### Nuevo Comando
```bash
make test-coverage  # pytest --cov=app --cov-report=html
```

---

## 3. Modularización CSS

### Estructura
```
app/static/css/
├── app.css              # Importa todos los módulos
├── base/
│   ├── reset.css
│   ├── variables.css
│   └── typography.css
├── components/
│   ├── buttons.css
│   ├── cards.css
│   ├── forms.css
│   ├── badges.css
│   ├── pills.css
│   ├── flash.css
│   └── chips.css
├── layouts/
│   ├── topbar.css
│   ├── bottom-nav.css
│   ├── menu-drawer.css
│   ├── page-wrap.css
│   └── grid.css
├── features/
│   ├── agenda.css
│   ├── timeline.css
│   ├── turno-card.css
│   ├── recurrence.css
│   └── search.css
└── utilities/
    ├── colors.css
    └── responsive.css
```

### Estrategia
- Extraer secciones del monolítico actual
- Mantener orden de cascada (base → components → layouts → features → utilities)
- No cambiar nombres de clases ni estilos

---

## 4. Review UX/UI

### Flujos a Auditar
| Flujo | Páginas |
|-------|---------|
| Auth | Login, Logout |
| Agenda | Vista día, navegación |
| Turnos | Nuevo, Editar, Detalle, Cancelar |
| Pacientes | Lista, Nuevo, Editar, Buscar |
| Profesionales | Lista, Detalle |
| Admin | Panel, Consultorios, Usuarios |

### Checklist por Página
- Elementos accesibles (a11y tree)
- Touch targets ≥ 44px
- Contraste de colores
- No overflow horizontal en mobile
- Labels en formularios
- Estados de error visibles
- Bottom nav no tapa contenido

### Output
`docs/ux-review-findings.md` con issues categorizados por severidad.

---

## 5. PWA y Mobile

### Manifest
```json
{
  "name": "ConsulApp",
  "short_name": "ConsulApp",
  "display": "standalone",
  "background_color": "#fafaf9",
  "theme_color": "#ea580c"
}
```

### Service Worker
- Cache de assets estáticos
- Network-first para HTML
- Soporte push notifications

### Gestos
| Gesto | Acción |
|-------|--------|
| Swipe izquierda | Día siguiente |
| Swipe derecha | Día anterior |
| Pull-to-refresh | Refrescar contenido |

### Archivos Nuevos
- `app/static/manifest.json`
- `app/static/sw.js`
- `app/static/js/sw-register.js`
- `app/static/icons/` (icon-192.png, icon-512.png, apple-touch-icon.png)

### Documentación
`docs/pwa-deployment.md` con guía de instalación.

---

## 6. Rediseño User-Profesional

### Cambio de Modelo
```
Antes: User (1) ----o (0..1) Profesional  [user_id nullable]
Después: User (1) ----• (1) Profesional   [user_id NOT NULL]
```

### Migración
1. Limpiar datos huérfanos
2. Crear profesionales para usuarios sin uno
3. ALTER COLUMN user_id SET NOT NULL

### Permisos
| Acción | Admin | Profesional |
|--------|-------|-------------|
| Ver lista profesionales | ✅ | ✅ (solo lectura) |
| Crear profesional | ✅ (via crear usuario) | ❌ |
| Editar profesional | ✅ (todos) | ✅ (solo el suyo) |
| Eliminar profesional | ✅ | ❌ |
| CRUD usuarios | ✅ | ❌ |

### Flujo Nuevo
- Admin crea usuario → se crea profesional automáticamente
- Profesional solo puede editar SU perfil (user_id = current_user.id)

---

## 7. Orden de Implementación

| # | Feature | Rama |
|---|---------|------|
| 001 | Git Workflow | `feature/001-git-workflow` |
| 002 | Tests Adicionales | `feature/002-tests-adicionales` |
| 003 | CSS Modularización | `feature/003-css-modularizacion` |
| 004 | UX Review | `feature/004-ux-review` |
| 005 | UX Fixes | `feature/005-ux-fixes` |
| 006 | PWA Base | `feature/006-pwa-base` |
| 007 | Gestos Mobile | `feature/007-gestos-mobile` |
| 008 | User-Profesional | `feature/008-user-profesional` |
| 009 | Push Notifications | `feature/009-push-notifications` |

---

## Entregables

### Documentación
- `CONTRIBUTING.md`
- `docs/plans/2026-03-05-consul-app-mejoras-design.md`
- `docs/ux-review-findings.md`
- `docs/pwa-deployment.md`

### Configuración
- `.github/workflows/ci.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- Branch protection rules

### Código
- 4+ archivos de tests nuevos
- 15+ archivos CSS modulares
- PWA completo (manifest, SW, iconos)
- Gestos mobile en app.js
- Migración Alembic para User-Profesional
