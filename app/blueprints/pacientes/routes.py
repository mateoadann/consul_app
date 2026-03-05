from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from app.extensions import db
from app.models import Paciente, Turno

from .forms import PacienteForm


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
            email=form.email.data.strip() if form.email.data else None,
            obra_social=form.obra_social.data.strip() if form.obra_social.data else None,
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
        paciente.email = form.email.data.strip() if form.email.data else None
        paciente.obra_social = form.obra_social.data.strip() if form.obra_social.data else None
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
