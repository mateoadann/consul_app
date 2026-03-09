# Importacion CSV + Obra Social + Campos Paciente — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reemplazar campo email por numero_afiliado, agregar campo apodo, convertir obra_social de texto libre a FK contra nueva entidad ObraSocial, crear CRUD de ObraSocial (admin), e importacion masiva de pacientes via CSV.

**Architecture:** Nueva tabla `obra_sociales` con relacion 1:N hacia `pacientes`. Blueprint `obra_sociales` con CRUD admin siguiendo el patron de `consultorios`. Importacion CSV en ruta nueva del blueprint `pacientes` con validacion fila a fila y resumen de resultados.

**Tech Stack:** Flask, SQLAlchemy, WTForms, HTMX, PostgreSQL, Alembic, pytest.

---

### Task 1: Modelo ObraSocial

**Files:**
- Create: `app/models/obra_social.py`
- Modify: `app/models/__init__.py`

**Step 1: Create model file**

```python
# app/models/obra_social.py
from app.extensions import db
from app.models.base import TimestampMixin


class ObraSocial(TimestampMixin, db.Model):
    __tablename__ = "obra_sociales"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)

    pacientes = db.relationship("Paciente", back_populates="obra_social")

    def __repr__(self) -> str:
        return f"<ObraSocial {self.nombre}>"
```

**Step 2: Register in models/__init__.py**

Add import and export of `ObraSocial`:

```python
from app.models.obra_social import ObraSocial
```

Add `"ObraSocial"` to `__all__`.

**Step 3: Commit**

```
feat: add ObraSocial model
```

---

### Task 2: Update Paciente model

**Files:**
- Modify: `app/models/paciente.py`

**Step 1: Update model**

Replace `email` and `obra_social` string fields with new fields:

```python
from app.extensions import db
from app.models.base import TimestampMixin


class Paciente(TimestampMixin, db.Model):
    __tablename__ = "pacientes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(15), nullable=False, unique=True)
    telefono = db.Column(db.String(50), nullable=True)
    apodo = db.Column(db.String(100), nullable=True)
    numero_afiliado = db.Column(db.Integer, nullable=True)
    obra_social_id = db.Column(db.Integer, db.ForeignKey("obra_sociales.id"), nullable=True)
    notas = db.Column(db.Text, nullable=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    obra_social = db.relationship("ObraSocial", back_populates="pacientes")
    turnos = db.relationship("Turno", back_populates="paciente", lazy="dynamic")

    @property
    def nombre_completo(self) -> str:
        return f"{self.apellido}, {self.nombre}"

    def __repr__(self) -> str:
        return f"<Paciente {self.apellido}, {self.nombre}>"
```

**Step 2: Commit**

```
feat: update Paciente model — replace email with numero_afiliado, add apodo, FK obra_social
```

---

### Task 3: Alembic migration

**Files:**
- Create: migration file via `make db-migrate`

**Step 1: Generate migration**

```bash
make db-migrate msg="add obra_sociales table and update pacientes fields"
```

**Step 2: Review generated migration**

Verify it contains:
- CREATE TABLE `obra_sociales` (id, nombre, created_at, updated_at)
- ADD COLUMN `apodo` String(100) nullable on `pacientes`
- ADD COLUMN `numero_afiliado` Integer nullable on `pacientes`
- ADD COLUMN `obra_social_id` Integer FK nullable on `pacientes`
- DROP COLUMN `email` from `pacientes`
- DROP COLUMN `obra_social` from `pacientes`

If auto-detect misses anything, edit the migration manually.

**Step 3: Apply migration**

```bash
make db-upgrade
```

**Step 4: Run existing tests to verify nothing breaks**

```bash
make docker-test
```

**Step 5: Commit**

```
feat: migration — add obra_sociales, update pacientes fields
```

---

### Task 4: CRUD ObraSocial — blueprint, forms, routes, template

**Files:**
- Create: `app/blueprints/obra_sociales/__init__.py` (empty)
- Create: `app/blueprints/obra_sociales/forms.py`
- Create: `app/blueprints/obra_sociales/routes.py`
- Create: `app/templates/obra_sociales/lista.html`
- Modify: `app/__init__.py` (register blueprint)
- Modify: `app/templates/admin/index.html` (add link)
- Modify: `app/templates/components/nav_bottom.html` (add obra_sociales to is_admin check)

**Step 1: Create form**

```python
# app/blueprints/obra_sociales/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class ObraSocialForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Guardar")
```

**Step 2: Create routes**

Follow the pattern from `app/blueprints/consultorios/routes.py`. Routes:
- `GET /obra-sociales` — lista (admin)
- `POST /obra-sociales/nuevo` — crear (admin)
- `GET/POST /obra-sociales/<id>/editar` — editar (admin)
- `POST /obra-sociales/<id>/eliminar` — eliminar (admin, only if no pacientes linked)

```python
# app/blueprints/obra_sociales/routes.py
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from app.extensions import db
from app.models import ObraSocial
from app.utils.decorators import role_required

from .forms import ObraSocialForm

obra_sociales_bp = Blueprint("obra_sociales", __name__, url_prefix="/obra-sociales")


@obra_sociales_bp.route("", methods=["GET"])
@login_required
@role_required("admin")
def lista():
    items = ObraSocial.query.order_by(ObraSocial.nombre).all()
    form = ObraSocialForm()
    return render_template("obra_sociales/lista.html", items=items, form=form)


@obra_sociales_bp.route("/nuevo", methods=["POST"])
@login_required
@role_required("admin")
def nuevo():
    form = ObraSocialForm()
    if form.validate_on_submit():
        existing = ObraSocial.query.filter_by(nombre=form.nombre.data.strip()).first()
        if existing:
            form.nombre.errors.append("Ya existe una obra social con ese nombre.")
            items = ObraSocial.query.order_by(ObraSocial.nombre).all()
            return render_template("obra_sociales/lista.html", form=form, items=items), 422
        os = ObraSocial(nombre=form.nombre.data.strip())
        db.session.add(os)
        db.session.commit()
        return redirect(url_for("obra_sociales.lista"))
    items = ObraSocial.query.order_by(ObraSocial.nombre).all()
    return render_template("obra_sociales/lista.html", form=form, items=items)


@obra_sociales_bp.route("/<int:obra_social_id>/editar", methods=["GET", "POST"])
@login_required
@role_required("admin")
def editar(obra_social_id):
    item = ObraSocial.query.get_or_404(obra_social_id)
    form = ObraSocialForm(obj=item)
    if form.validate_on_submit():
        dup = ObraSocial.query.filter(
            ObraSocial.nombre == form.nombre.data.strip(),
            ObraSocial.id != item.id,
        ).first()
        if dup:
            form.nombre.errors.append("Ya existe una obra social con ese nombre.")
            items = ObraSocial.query.order_by(ObraSocial.nombre).all()
            return render_template("obra_sociales/lista.html", form=form, items=items, item_edit=item), 422
        item.nombre = form.nombre.data.strip()
        db.session.commit()
        return redirect(url_for("obra_sociales.lista"))
    items = ObraSocial.query.order_by(ObraSocial.nombre).all()
    return render_template("obra_sociales/lista.html", form=form, items=items, item_edit=item)


@obra_sociales_bp.route("/<int:obra_social_id>/eliminar", methods=["POST"])
@login_required
@role_required("admin")
def eliminar(obra_social_id):
    item = ObraSocial.query.get_or_404(obra_social_id)
    if item.pacientes:
        flash("No se puede eliminar: hay pacientes con esta obra social.", "error")
        return redirect(url_for("obra_sociales.lista"))
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("obra_sociales.lista"))
```

**Step 3: Create template**

```html
{# app/templates/obra_sociales/lista.html #}
{% extends 'base.html' %}
{% block title %}Obras Sociales - ConsulApp{% endblock %}
{% block content %}
<section class="card">
  <div class="card-header-row">
    <h1>Obras Sociales</h1>
    <a class="btn btn-ghost" href="{{ url_for('admin.index') }}">Volver a admin</a>
  </div>

  <form method="post" action="{{ url_for('obra_sociales.editar', obra_social_id=item_edit.id) if item_edit else url_for('obra_sociales.nuevo') }}" class="inline-form">
    {{ form.hidden_tag() }}
    {{ form.nombre(class_='input', placeholder='Nombre de la obra social') }}
    {% for error in form.nombre.errors %}<small class="field-error">{{ error }}</small>{% endfor %}
    {{ form.submit(class_='btn btn-primary') }}
  </form>

  <div class="list-wrap">
    {% for item in items %}
      <div class="list-item list-item-row">
        <strong>{{ item.nombre }}</strong>
        <div>
          <a href="{{ url_for('obra_sociales.editar', obra_social_id=item.id) }}" class="btn btn-ghost">Editar</a>
          <form method="post" action="{{ url_for('obra_sociales.eliminar', obra_social_id=item.id) }}" style="display:inline"
                onsubmit="return confirm('Eliminar esta obra social?')">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <button class="btn btn-ghost" type="submit">Eliminar</button>
          </form>
        </div>
      </div>
    {% else %}
      <p class="muted">No hay obras sociales cargadas.</p>
    {% endfor %}
  </div>
</section>
{% endblock %}
```

**Step 4: Register blueprint in `app/__init__.py`**

In `register_blueprints()`, add:

```python
from .blueprints.obra_sociales.routes import obra_sociales_bp
app.register_blueprint(obra_sociales_bp)
```

**Step 5: Add link in admin panel**

In `app/templates/admin/index.html`, add after the Consultorios link:

```html
<a class="list-item" href="{{ url_for('obra_sociales.lista') }}">
  <strong>Obras Sociales</strong>
  <small>Gestionar obras sociales disponibles</small>
</a>
```

**Step 6: Update nav_bottom.html is_admin check**

In line 5 of `app/templates/components/nav_bottom.html`, add `obra_sociales.` to the check:

```
{% set is_admin = endpoint.startswith('admin.') or endpoint.startswith('consultorios.') or endpoint.startswith('profesionales.') or endpoint.startswith('obra_sociales.') %}
```

**Step 7: Run tests**

```bash
make docker-test
```

**Step 8: Commit**

```
feat: add ObraSocial CRUD blueprint (admin only)
```

---

### Task 5: Update Paciente forms and templates

**Files:**
- Modify: `app/blueprints/pacientes/forms.py`
- Modify: `app/blueprints/pacientes/routes.py`
- Modify: `app/templates/pacientes/nuevo.html`
- Modify: `app/templates/pacientes/detalle.html`

**Step 1: Update form**

Replace `PacienteForm` — remove `email`, change `obra_social` to `SelectField`, add `apodo` and `numero_afiliado`:

```python
# app/blueprints/pacientes/forms.py
from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class PacienteForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    apellido = StringField("Apellido", validators=[DataRequired(), Length(max=100)])
    dni = StringField("DNI", validators=[DataRequired(), Length(max=15)])
    telefono = StringField("Telefono", validators=[Optional(), Length(max=50)])
    apodo = StringField("Apodo", validators=[Optional(), Length(max=100)])
    numero_afiliado = IntegerField("Numero de afiliado", validators=[Optional(), NumberRange(min=0)])
    obra_social_id = SelectField("Obra social", coerce=int, validators=[Optional()])
    notas = TextAreaField("Notas", validators=[Optional()])
    activo = BooleanField("Activo", default=True)
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import ObraSocial
        choices = [(0, "— Sin obra social —")] + [
            (os.id, os.nombre) for os in ObraSocial.query.order_by(ObraSocial.nombre).all()
        ]
        self.obra_social_id.choices = choices
```

**Step 2: Update routes**

In `app/blueprints/pacientes/routes.py`:

- In `nuevo()`: replace `email=...` and `obra_social=...` with new fields. Treat `obra_social_id == 0` as `None`.
- In `editar()`: same replacements.

For `nuevo()` the Paciente creation becomes:

```python
paciente = Paciente(
    nombre=form.nombre.data.strip(),
    apellido=form.apellido.data.strip(),
    dni=form.dni.data.strip(),
    telefono=form.telefono.data.strip() if form.telefono.data else None,
    apodo=form.apodo.data.strip() if form.apodo.data else None,
    numero_afiliado=form.numero_afiliado.data or None,
    obra_social_id=form.obra_social_id.data or None,
    notas=form.notas.data.strip() if form.notas.data else None,
    activo=form.activo.data,
)
```

For `editar()` the field updates become:

```python
paciente.nombre = form.nombre.data.strip()
paciente.apellido = form.apellido.data.strip()
paciente.dni = form.dni.data.strip()
paciente.telefono = form.telefono.data.strip() if form.telefono.data else None
paciente.apodo = form.apodo.data.strip() if form.apodo.data else None
paciente.numero_afiliado = form.numero_afiliado.data or None
paciente.obra_social_id = form.obra_social_id.data or None
paciente.notas = form.notas.data.strip() if form.notas.data else None
paciente.activo = form.activo.data
```

**Step 3: Update nuevo.html template**

Replace the email and obra_social lines:

```html
<label>{{ form.telefono.label }} {{ form.telefono(class_='input') }}</label>
<label>{{ form.apodo.label }} {{ form.apodo(class_='input') }}</label>
<label>{{ form.numero_afiliado.label }} {{ form.numero_afiliado(class_='input', type='number') }}</label>
<label>{{ form.obra_social_id.label }} {{ form.obra_social_id(class_='input') }}</label>
<label>{{ form.notas.label }} {{ form.notas(class_='input', rows='4') }}</label>
```

**Step 4: Update detalle.html template**

Replace email/obra_social display:

```html
<dl class="detail-grid">
  <dt>DNI</dt><dd>{{ paciente.dni }}</dd>
  <dt>Telefono</dt><dd>{{ paciente.telefono or '-' }}</dd>
  <dt>Apodo</dt><dd>{{ paciente.apodo or '-' }}</dd>
  <dt>Nro. afiliado</dt><dd>{{ paciente.numero_afiliado or '-' }}</dd>
  <dt>Obra social</dt><dd>{{ paciente.obra_social.nombre if paciente.obra_social else '-' }}</dd>
</dl>
```

**Step 5: Run tests**

```bash
make docker-test
```

**Step 6: Commit**

```
feat: update paciente forms/templates for new fields
```

---

### Task 6: Update tests and seed

**Files:**
- Modify: `tests/test_pacientes.py`
- Modify: `tests/conftest.py` (add obra_social fixture if needed)
- Modify: `seed.py`

**Step 1: Update test_crear_paciente**

```python
def test_crear_paciente(client):
    user = User(username="pro1", role="profesional", nombre="Pro Uno", activo=True)
    user.set_password("secret")
    db.session.add(user)
    db.session.commit()

    client.post("/auth/login", data={"username": "pro1", "password": "secret"})

    response = client.post(
        "/pacientes/nuevo",
        data={
            "nombre": "Pedro",
            "apellido": "Perez",
            "dni": "30000001",
            "telefono": "111",
            "apodo": "",
            "numero_afiliado": "",
            "obra_social_id": "0",
            "notas": "",
            "activo": "y",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert Paciente.query.filter_by(dni="30000001").first() is not None
```

**Step 2: Update seed.py**

Update `get_or_create_paciente` to remove `email` and `obra_social` string params, use new fields:

```python
def get_or_create_paciente(nombre, apellido, dni, telefono):
    paciente = Paciente.query.filter_by(dni=dni).first()
    if paciente:
        return paciente
    paciente = Paciente(
        nombre=nombre,
        apellido=apellido,
        dni=dni,
        telefono=telefono,
        notas=None,
        activo=True,
    )
    db.session.add(paciente)
    db.session.flush()
    return paciente
```

Also add ObraSocial import and seed some default values:

```python
from app.models import Consultorio, ObraSocial, Paciente, Profesional, Turno, User

# Inside run_seed(), after creating consultorios:
for nombre in ["OSDE", "Swiss Medical", "Galeno", "Particular"]:
    if not ObraSocial.query.filter_by(nombre=nombre).first():
        db.session.add(ObraSocial(nombre=nombre))
db.session.flush()
```

**Step 3: Run tests**

```bash
make docker-test
```

**Step 4: Commit**

```
feat: update tests and seed for new paciente fields
```

---

### Task 7: CSV import feature

**Files:**
- Modify: `app/blueprints/pacientes/routes.py` (add import routes)
- Modify: `app/blueprints/pacientes/forms.py` (add import form)
- Create: `app/templates/pacientes/importar.html`

**Step 1: Add import form**

```python
# Add to app/blueprints/pacientes/forms.py
from flask_wtf.file import FileAllowed, FileField, FileRequired


class ImportarCSVForm(FlaskForm):
    archivo = FileField("Archivo CSV", validators=[FileRequired(), FileAllowed(["csv"], "Solo archivos CSV")])
    submit = SubmitField("Importar")
```

**Step 2: Add import routes**

Add to `app/blueprints/pacientes/routes.py`:

```python
import csv
import io
from app.models import ObraSocial
from app.utils.decorators import role_required
from .forms import ImportarCSVForm


@pacientes_bp.route("/importar", methods=["GET", "POST"])
@login_required
@role_required("admin")
def importar():
    form = ImportarCSVForm()
    resultados = None

    if form.validate_on_submit():
        archivo = form.archivo.data
        stream = io.StringIO(archivo.stream.read().decode("utf-8-sig"))
        reader = csv.DictReader(stream)

        creados = 0
        saltados = 0
        errores = []

        obra_social_ids = {os.id for os in ObraSocial.query.all()}

        for i, row in enumerate(reader, start=2):
            nombre = (row.get("nombre") or "").strip()
            apellido = (row.get("apellido") or "").strip()
            dni = (row.get("dni") or "").strip()

            if not nombre or not apellido or not dni:
                errores.append(f"Fila {i}: nombre, apellido y dni son obligatorios")
                continue

            if Paciente.query.filter_by(dni=dni).first():
                saltados += 1
                continue

            telefono = (row.get("telefono") or "").strip() or None
            apodo = (row.get("apodo") or "").strip() or None
            notas = (row.get("notas") or "").strip() or None

            numero_afiliado = None
            raw_nro = (row.get("numero_afiliado") or "").strip()
            if raw_nro:
                if raw_nro.isdigit():
                    numero_afiliado = int(raw_nro)
                else:
                    errores.append(f"Fila {i}: numero_afiliado debe ser numerico")
                    continue

            obra_social_id = None
            raw_os = (row.get("obra_social_id") or "").strip()
            if raw_os:
                if raw_os.isdigit() and int(raw_os) in obra_social_ids:
                    obra_social_id = int(raw_os)
                else:
                    errores.append(f"Fila {i}: obra_social_id '{raw_os}' no existe")
                    continue

            paciente = Paciente(
                nombre=nombre,
                apellido=apellido,
                dni=dni,
                telefono=telefono,
                apodo=apodo,
                numero_afiliado=numero_afiliado,
                obra_social_id=obra_social_id,
                notas=notas,
                activo=True,
            )
            db.session.add(paciente)
            creados += 1

        if creados > 0:
            db.session.commit()

        resultados = {"creados": creados, "saltados": saltados, "errores": errores}

    return render_template("pacientes/importar.html", form=form, resultados=resultados)
```

**Step 3: Create import template**

```html
{# app/templates/pacientes/importar.html #}
{% extends 'base.html' %}
{% block title %}Importar Pacientes - ConsulApp{% endblock %}
{% block content %}
<section class="card">
  <div class="card-header-row">
    <h1>Importar pacientes</h1>
    <a class="btn btn-ghost" href="{{ url_for('pacientes.lista') }}">Volver</a>
  </div>

  <form method="post" enctype="multipart/form-data" class="stack">
    {{ form.hidden_tag() }}
    <label>{{ form.archivo.label }} {{ form.archivo(class_='input') }}</label>
    {% for error in form.archivo.errors %}<small class="field-error">{{ error }}</small>{% endfor %}
    <p class="muted">Formato: nombre,apellido,dni,telefono,numero_afiliado,obra_social_id,notas,apodo</p>
    {{ form.submit(class_='btn btn-primary') }}
  </form>

  {% if resultados %}
  <div class="stack" style="margin-top: 1.5rem">
    <h2>Resultado</h2>
    <dl class="detail-grid">
      <dt>Creados</dt><dd>{{ resultados.creados }}</dd>
      <dt>Saltados (DNI existente)</dt><dd>{{ resultados.saltados }}</dd>
      <dt>Errores</dt><dd>{{ resultados.errores|length }}</dd>
    </dl>
    {% if resultados.errores %}
    <details>
      <summary>Ver errores</summary>
      <ul>
        {% for e in resultados.errores %}
          <li>{{ e }}</li>
        {% endfor %}
      </ul>
    </details>
    {% endif %}
  </div>
  {% endif %}
</section>
{% endblock %}
```

**Step 4: Add link to import from pacientes list**

In `app/templates/pacientes/lista.html`, add import button next to "+ Nuevo":

```html
<div class="card-header-row">
  <h1>Pacientes</h1>
  <div>
    {% if current_user.role == 'admin' %}
      <a href="{{ url_for('pacientes.importar') }}" class="btn btn-ghost">Importar CSV</a>
    {% endif %}
    <a href="{{ url_for('pacientes.nuevo') }}" class="btn btn-primary">+ Nuevo</a>
  </div>
</div>
```

**Step 5: Run tests**

```bash
make docker-test
```

**Step 6: Commit**

```
feat: add CSV import for pacientes (admin only)
```

---

### Task 8: Write test for CSV import

**Files:**
- Modify: `tests/test_pacientes.py`

**Step 1: Add import test**

```python
def test_importar_csv(client, admin_user):
    from app.models import ObraSocial
    os = ObraSocial(nombre="OSDE")
    db.session.add(os)
    db.session.commit()

    client.post("/auth/login", data={"username": "admin_test", "password": "admin123"})

    csv_content = f"nombre,apellido,dni,telefono,numero_afiliado,obra_social_id,notas,apodo\nJuan,Perez,40000001,1155551234,12345,{os.id},nota test,Juancito\nMaria,Lopez,40000002,,,,,"
    data = {
        "archivo": (io.BytesIO(csv_content.encode("utf-8")), "pacientes.csv"),
    }
    response = client.post("/pacientes/importar", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    assert Paciente.query.filter_by(dni="40000001").first() is not None
    assert Paciente.query.filter_by(dni="40000002").first() is not None
    p1 = Paciente.query.filter_by(dni="40000001").first()
    assert p1.numero_afiliado == 12345
    assert p1.obra_social_id == os.id
    assert p1.apodo == "Juancito"


def test_importar_csv_skip_duplicate(client, admin_user):
    client.post("/auth/login", data={"username": "admin_test", "password": "admin123"})

    existing = Paciente(nombre="Existing", apellido="Patient", dni="50000001", activo=True)
    db.session.add(existing)
    db.session.commit()

    csv_content = "nombre,apellido,dni,telefono,numero_afiliado,obra_social_id,notas,apodo\nExisting,Patient,50000001,,,,,"
    data = {"archivo": (io.BytesIO(csv_content.encode("utf-8")), "pacientes.csv")}
    response = client.post("/pacientes/importar", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    assert b"1" in response.data  # saltados count
```

Add `import io` at the top of the test file.

**Step 2: Run tests**

```bash
make docker-test
```

**Step 3: Commit**

```
test: add CSV import tests for pacientes
```

---

### Task 9: Final verification and PR

**Step 1: Run full test suite**

```bash
make docker-test
```

**Step 2: Commit any remaining fixes**

**Step 3: Create PR**

```bash
gh pr create --title "feat: obra social entity, paciente field updates, CSV import" --body "..."
```
