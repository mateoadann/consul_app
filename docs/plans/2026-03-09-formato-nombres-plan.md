# Formato de Nombres en Agenda - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow admin to configure how patient and professional names display in agenda chips, with live preview.

**Architecture:** New `AppConfig` key-value model stores global settings. A Jinja filter `display_name` reads the config (cached per-request in `g`) and formats entity names. Admin UI at `/admin/formato-nombres` with JS-powered live preview.

**Tech Stack:** Flask, SQLAlchemy, WTForms, Jinja2, vanilla JS

---

### Task 1: Add `apodo` field to Profesional model

**Files:**
- Modify: `app/models/profesional.py`
- Create: `migrations/versions/6b2c3d4e5f6g_add_apodo_profesional_and_app_config.py`

**Step 1: Add `apodo` field to Profesional model**

In `app/models/profesional.py`, add after `email` line:

```python
apodo = db.Column(db.String(100), nullable=True)
```

**Step 2: Create migration**

Run: `make db-migrate msg="add apodo to profesional and app_config table"`

Then manually edit the migration to also include the `app_config` table (Task 2). Or create two separate migrations.

**Step 3: Commit**

```bash
git add app/models/profesional.py migrations/
git commit -m "feat: add apodo field to profesional model"
```

---

### Task 2: Create AppConfig model

**Files:**
- Create: `app/models/app_config.py`
- Modify: `app/models/__init__.py`

**Step 1: Create the model**

Create `app/models/app_config.py`:

```python
from app.extensions import db


class AppConfig(db.Model):
    __tablename__ = "app_config"

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(255), nullable=False)

    @staticmethod
    def get(key: str, default: str = "") -> str:
        row = AppConfig.query.get(key)
        return row.value if row else default

    @staticmethod
    def set(key: str, value: str) -> None:
        row = AppConfig.query.get(key)
        if row:
            row.value = value
        else:
            row = AppConfig(key=key, value=value)
            db.session.add(row)
```

**Step 2: Register in `__init__`**

In `app/models/__init__.py`, add import and `__all__` entry:

```python
from app.models.app_config import AppConfig
```

Add `"AppConfig"` to `__all__`.

**Step 3: Create migration**

The migration should create both the `app_config` table and add `apodo` to `profesionales`:

```python
def upgrade():
    op.create_table(
        "app_config",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.String(255), nullable=False),
    )
    op.add_column("profesionales", sa.Column("apodo", sa.String(100), nullable=True))

def downgrade():
    op.drop_column("profesionales", "apodo")
    op.drop_table("app_config")
```

**Step 4: Apply migration and commit**

```bash
make db-upgrade
git add app/models/app_config.py app/models/__init__.py migrations/
git commit -m "feat: add AppConfig model and apodo to profesional"
```

---

### Task 3: Create display_name helper and Jinja filter

**Files:**
- Modify: `app/utils/formatting.py`
- Modify: `app/__init__.py`

**Step 1: Add the formatting function**

In `app/utils/formatting.py`, add at the end:

```python
FORMATO_NOMBRE_OPTIONS = {
    "nombre": "Nombre",
    "nombre_apellido": "Nombre Apellido",
    "nombre_inicial": "Nombre + inicial",
    "apodo": "Apodo",
    "apodo_inicial": "Apodo + inicial",
}

FORMATO_NOMBRE_DEFAULT = "nombre_inicial"


def format_display_name(entity, format_key: str) -> str:
    nombre = getattr(entity, "nombre", "")
    apellido = getattr(entity, "apellido", "")
    apodo = getattr(entity, "apodo", None) or ""
    inicial = f"{apellido[0]}." if apellido else ""

    fallback = f"{nombre} {inicial}".strip()

    if format_key == "nombre":
        return nombre
    elif format_key == "nombre_apellido":
        return f"{nombre} {apellido}".strip()
    elif format_key == "nombre_inicial":
        return fallback
    elif format_key == "apodo":
        return apodo if apodo else fallback
    elif format_key == "apodo_inicial":
        if apodo:
            return f"{apodo} {inicial}".strip()
        return fallback

    return fallback
```

**Step 2: Register Jinja filters in `app/__init__.py`**

In the `register_request_hooks` function, add a `before_request` to cache config in `g`:

```python
from flask import g

@app.before_request
def load_display_name_config():
    from .models.app_config import AppConfig
    from .utils.formatting import FORMATO_NOMBRE_DEFAULT
    g.fmt_paciente = AppConfig.get("formato_nombre_paciente", FORMATO_NOMBRE_DEFAULT)
    g.fmt_profesional = AppConfig.get("formato_nombre_profesional", FORMATO_NOMBRE_DEFAULT)
```

In `register_template_filters`, add two filters:

```python
from .utils.formatting import format_display_name

def _display_name_paciente(paciente):
    from flask import g
    fmt = getattr(g, "fmt_paciente", "nombre_inicial")
    return format_display_name(paciente, fmt)

def _display_name_profesional(profesional):
    from flask import g
    fmt = getattr(g, "fmt_profesional", "nombre_inicial")
    return format_display_name(profesional, fmt)

app.jinja_env.filters["display_name_paciente"] = _display_name_paciente
app.jinja_env.filters["display_name_profesional"] = _display_name_profesional
```

**Step 3: Commit**

```bash
git add app/utils/formatting.py app/__init__.py
git commit -m "feat: add display_name formatting helper and jinja filters"
```

---

### Task 4: Update agenda templates to use new filters

**Files:**
- Modify: `app/templates/agenda/_grilla.html`
- Modify: `app/templates/agenda/_slot.html`
- Modify: `app/templates/agenda/_timeline.html`
- Modify: `app/templates/turnos/_ocupados.html`

**Step 1: Update `_grilla.html`**

Replace:
```html
<strong>{{ turno.paciente.apellido }}</strong>
<small>{{ turno.profesional.apellido }}</small>
```
With:
```html
<strong>{{ turno.paciente|display_name_paciente }}</strong>
<small>{{ turno.profesional|display_name_profesional }}</small>
```

**Step 2: Update `_slot.html`**

Same replacement as above.

**Step 3: Update `_timeline.html`**

Replace:
```html
{{ turno.paciente.apellido }}{% if not consultorio_id_filter %} · {{ turno.profesional.apellido }}{% endif %}
```
With:
```html
{{ turno.paciente|display_name_paciente }}{% if not consultorio_id_filter %} · {{ turno.profesional|display_name_profesional }}{% endif %}
```

**Step 4: Update `_ocupados.html`**

Replace:
```html
<small>{{ turno.paciente.apellido }}</small>
```
With:
```html
<small>{{ turno.paciente|display_name_paciente }}</small>
```

**Step 5: Commit**

```bash
git add app/templates/agenda/_grilla.html app/templates/agenda/_slot.html app/templates/agenda/_timeline.html app/templates/turnos/_ocupados.html
git commit -m "feat: use display_name filters in agenda templates"
```

---

### Task 5: Admin UI — formato de nombres page

**Files:**
- Create: `app/templates/admin/formato_nombres.html`
- Modify: `app/blueprints/admin/routes.py`
- Modify: `app/templates/admin/index.html`

**Step 1: Add route**

In `app/blueprints/admin/routes.py`, add:

```python
from app.models import AppConfig
from app.utils.formatting import FORMATO_NOMBRE_OPTIONS, FORMATO_NOMBRE_DEFAULT

@admin_bp.route("/formato-nombres", methods=["GET", "POST"])
@login_required
@role_required("admin")
def formato_nombres():
    if request.method == "POST":
        fmt_paciente = request.form.get("formato_paciente", FORMATO_NOMBRE_DEFAULT)
        fmt_profesional = request.form.get("formato_profesional", FORMATO_NOMBRE_DEFAULT)

        if fmt_paciente in FORMATO_NOMBRE_OPTIONS:
            AppConfig.set("formato_nombre_paciente", fmt_paciente)
        if fmt_profesional in FORMATO_NOMBRE_OPTIONS:
            AppConfig.set("formato_nombre_profesional", fmt_profesional)

        db.session.commit()
        flash("Formato de nombres actualizado.", "success")
        return redirect(url_for("admin.formato_nombres"))

    current_paciente = AppConfig.get("formato_nombre_paciente", FORMATO_NOMBRE_DEFAULT)
    current_profesional = AppConfig.get("formato_nombre_profesional", FORMATO_NOMBRE_DEFAULT)

    return render_template(
        "admin/formato_nombres.html",
        options=FORMATO_NOMBRE_OPTIONS,
        current_paciente=current_paciente,
        current_profesional=current_profesional,
    )
```

**Step 2: Create template**

Create `app/templates/admin/formato_nombres.html`:

```html
{% extends 'base.html' %}
{% block title %}Formato de Nombres - ConsulApp{% endblock %}
{% block content %}
<section class="card">
  <div class="card-header-row">
    <h1>Formato de nombres</h1>
    <a class="btn btn-ghost" href="{{ url_for('admin.index') }}">Volver</a>
  </div>

  <form method="post" class="stack" style="margin-top: 1rem">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

    <label>
      Paciente
      <select name="formato_paciente" class="input" id="fmt-paciente" onchange="updatePreview()">
        {% for key, label in options.items() %}
          <option value="{{ key }}" {% if key == current_paciente %}selected{% endif %}>{{ label }}</option>
        {% endfor %}
      </select>
    </label>
    <div class="preview-box" id="preview-paciente"></div>

    <label>
      Profesional
      <select name="formato_profesional" class="input" id="fmt-profesional" onchange="updatePreview()">
        {% for key, label in options.items() %}
          <option value="{{ key }}" {% if key == current_profesional %}selected{% endif %}>{{ label }}</option>
        {% endfor %}
      </select>
    </label>
    <div class="preview-box" id="preview-profesional"></div>

    <button type="submit" class="btn btn-primary">Guardar</button>
  </form>
</section>

<script>
  const examples = {
    paciente: { nombre: "Maria", apellido: "Lopez", apodo: "Mari" },
    profesional: { nombre: "Carla", apellido: "Garcia", apodo: "Dra. Car" },
  };

  function formatName(entity, key) {
    const nombre = entity.nombre;
    const apellido = entity.apellido;
    const apodo = entity.apodo || "";
    const inicial = apellido ? apellido[0] + "." : "";
    const fallback = (nombre + " " + inicial).trim();

    if (key === "nombre") return nombre;
    if (key === "nombre_apellido") return (nombre + " " + apellido).trim();
    if (key === "nombre_inicial") return fallback;
    if (key === "apodo") return apodo || fallback;
    if (key === "apodo_inicial") return apodo ? (apodo + " " + inicial).trim() : fallback;
    return fallback;
  }

  function updatePreview() {
    const fmtP = document.getElementById("fmt-paciente").value;
    const fmtR = document.getElementById("fmt-profesional").value;
    document.getElementById("preview-paciente").textContent = formatName(examples.paciente, fmtP);
    document.getElementById("preview-profesional").textContent = formatName(examples.profesional, fmtR);
  }

  updatePreview();
</script>
{% endblock %}
```

**Step 3: Add link in admin index**

In `app/templates/admin/index.html`, add before the closing `</div>` of list-wrap:

```html
<a class="list-item" href="{{ url_for('admin.formato_nombres') }}">
  <strong>Formato de nombres</strong>
  <small>Como se muestran pacientes y profesionales en la agenda</small>
</a>
```

**Step 4: Add CSS for preview box**

Add inline or in a CSS file:

```css
.preview-box {
  background: var(--muted-bg, #f5f5f5);
  border-radius: var(--radius);
  padding: 0.6rem 0.8rem;
  font-weight: 600;
  font-size: 0.95rem;
}
```

**Step 5: Commit**

```bash
git add app/blueprints/admin/routes.py app/templates/admin/formato_nombres.html app/templates/admin/index.html
git commit -m "feat: admin UI for name format configuration with live preview"
```

---

### Task 6: Update profesional forms to include apodo

**Files:**
- Modify: `app/blueprints/admin/forms.py` (UsuarioForm, UsuarioEditForm)
- Modify: `app/templates/admin/usuario_form.html`
- Modify: `app/blueprints/admin/routes.py` (nuevo_usuario, editar_usuario)

**Step 1: Add apodo to forms**

In `app/blueprints/admin/forms.py`, add to both UsuarioForm and UsuarioEditForm:

```python
apodo = StringField("Apodo", validators=[Optional()])
```

**Step 2: Update routes**

In `nuevo_usuario`, when creating Profesional, add:
```python
profesional = Profesional(
    nombre=form.nombre.data.strip(),
    apellido=form.apellido.data.strip(),
    apodo=form.apodo.data.strip() if form.apodo.data else None,
    user_id=user.id,
)
```

In `editar_usuario` GET, add:
```python
if request.method == "GET" and user.profesional:
    form.apodo.data = user.profesional.apodo
```

In `editar_usuario` POST, add:
```python
if user.profesional:
    user.profesional.apodo = form.apodo.data.strip() if form.apodo.data else None
```

**Step 3: Update template**

In `app/templates/admin/usuario_form.html`, add apodo field in the profesional section.

**Step 4: Commit**

```bash
git add app/blueprints/admin/forms.py app/blueprints/admin/routes.py app/templates/admin/usuario_form.html
git commit -m "feat: add apodo field to profesional forms"
```

---

### Task 7: Write tests

**Files:**
- Create: `tests/test_display_name.py`

**Step 1: Write tests for format_display_name**

```python
import pytest
from app.utils.formatting import format_display_name


class FakeEntity:
    def __init__(self, nombre, apellido, apodo=None):
        self.nombre = nombre
        self.apellido = apellido
        self.apodo = apodo


def test_format_nombre():
    e = FakeEntity("Pedro", "Gomez", "Pedrito")
    assert format_display_name(e, "nombre") == "Pedro"


def test_format_nombre_apellido():
    e = FakeEntity("Pedro", "Gomez")
    assert format_display_name(e, "nombre_apellido") == "Pedro Gomez"


def test_format_nombre_inicial():
    e = FakeEntity("Pedro", "Gomez")
    assert format_display_name(e, "nombre_inicial") == "Pedro G."


def test_format_apodo_with_apodo():
    e = FakeEntity("Pedro", "Gomez", "Pedrito")
    assert format_display_name(e, "apodo") == "Pedrito"


def test_format_apodo_fallback():
    e = FakeEntity("Pedro", "Gomez")
    assert format_display_name(e, "apodo") == "Pedro G."


def test_format_apodo_inicial_with_apodo():
    e = FakeEntity("Pedro", "Gomez", "Pedrito")
    assert format_display_name(e, "apodo_inicial") == "Pedrito G."


def test_format_apodo_inicial_fallback():
    e = FakeEntity("Pedro", "Gomez")
    assert format_display_name(e, "apodo_inicial") == "Pedro G."


def test_format_unknown_key_uses_fallback():
    e = FakeEntity("Pedro", "Gomez")
    assert format_display_name(e, "invalid") == "Pedro G."
```

**Step 2: Run tests**

```bash
pytest tests/test_display_name.py -vv -rA
```

**Step 3: Commit**

```bash
git add tests/test_display_name.py
git commit -m "test: add display_name formatting tests"
```
