import csv
import io

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from app.extensions import db
from app.models import ObraSocial, Paciente, Turno
from app.utils.decorators import role_required

from .forms import ImportarCSVForm, PacienteForm


pacientes_bp = Blueprint("pacientes", __name__, url_prefix="/pacientes")


@pacientes_bp.route("", methods=["GET"])
@login_required
def lista():
    q = (request.args.get("q") or "").strip()
    page = request.args.get("page", default=1, type=int)

    query = Paciente.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Paciente.nombre.ilike(like),
                Paciente.apellido.ilike(like),
                Paciente.dni.ilike(like),
            )
        )

    pagination = query.order_by(Paciente.apellido, Paciente.nombre).paginate(
        page=page,
        per_page=20,
        error_out=False,
    )
    return render_template("pacientes/lista.html", pagination=pagination, q=q)


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


@pacientes_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    form = PacienteForm()
    if form.validate_on_submit():
        exists = Paciente.query.filter_by(dni=form.dni.data.strip()).first()
        if exists:
            form.dni.errors.append("Ya existe un paciente con ese DNI.")
            return render_template("pacientes/nuevo.html", form=form), 422

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
        db.session.add(paciente)
        db.session.commit()
        return redirect(url_for("pacientes.detalle", paciente_id=paciente.id))

    return render_template("pacientes/nuevo.html", form=form)


@pacientes_bp.route("/<int:paciente_id>", methods=["GET"])
@login_required
def detalle(paciente_id):
    paciente = Paciente.query.get_or_404(paciente_id)
    turnos = (
        Turno.query.filter_by(paciente_id=paciente.id)
        .order_by(Turno.created_at.desc())
        .limit(25)
        .all()
    )
    return render_template("pacientes/detalle.html", paciente=paciente, turnos=turnos)


@pacientes_bp.route("/<int:paciente_id>/editar", methods=["GET", "POST"])
@login_required
def editar(paciente_id):
    paciente = Paciente.query.get_or_404(paciente_id)
    form = PacienteForm(obj=paciente)

    if form.validate_on_submit():
        duplicate = (
            Paciente.query.filter(Paciente.dni == form.dni.data.strip(), Paciente.id != paciente.id)
            .limit(1)
            .first()
        )
        if duplicate:
            form.dni.errors.append("Ya existe un paciente con ese DNI.")
            return render_template("pacientes/nuevo.html", form=form, paciente=paciente), 422

        paciente.nombre = form.nombre.data.strip()
        paciente.apellido = form.apellido.data.strip()
        paciente.dni = form.dni.data.strip()
        paciente.telefono = form.telefono.data.strip() if form.telefono.data else None
        paciente.apodo = form.apodo.data.strip() if form.apodo.data else None
        paciente.numero_afiliado = form.numero_afiliado.data or None
        paciente.obra_social_id = form.obra_social_id.data or None
        paciente.notas = form.notas.data.strip() if form.notas.data else None
        paciente.activo = form.activo.data
        db.session.commit()
        return redirect(url_for("pacientes.detalle", paciente_id=paciente.id))

    return render_template("pacientes/nuevo.html", form=form, paciente=paciente)


@pacientes_bp.route("/htmx/buscar", methods=["GET"])
@login_required
def buscar_htmx():
    q = (request.args.get("q") or request.args.get("paciente_query") or "").strip()
    if len(q) < 2:
        return render_template("pacientes/_search_results.html", pacientes=[])

    like = f"%{q}%"
    pacientes = (
        Paciente.query.filter(
            or_(
                Paciente.nombre.ilike(like),
                Paciente.apellido.ilike(like),
                Paciente.dni.ilike(like),
            )
        )
        .order_by(Paciente.apellido, Paciente.nombre)
        .limit(10)
        .all()
    )
    return render_template("pacientes/_search_results.html", pacientes=pacientes)


@pacientes_bp.route("/htmx/validar-dni", methods=["GET"])
@login_required
def validar_dni_htmx():
    dni = (request.args.get("dni") or "").strip()
    paciente_id = request.args.get("paciente_id", type=int)

    if not dni:
        return "<small class='field-help'>Ingresa un DNI</small>"

    query = Paciente.query.filter(Paciente.dni == dni)
    if paciente_id:
        query = query.filter(Paciente.id != paciente_id)

    exists = query.first() is not None
    if exists:
        return "<small class='field-error'>DNI ya registrado</small>", 409
    return "<small class='field-ok'>DNI disponible</small>"
