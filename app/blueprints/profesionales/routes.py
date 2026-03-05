from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from app.extensions import db
from app.models import Profesional
from app.utils.decorators import role_required

from .forms import ProfesionalForm


profesionales_bp = Blueprint("profesionales", __name__, url_prefix="/profesionales")


@profesionales_bp.route("", methods=["GET"])
@login_required
@role_required("admin")
def lista():
    profesionales = Profesional.query.order_by(Profesional.apellido, Profesional.nombre).all()
    return render_template("profesionales/lista.html", profesionales=profesionales)


@profesionales_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@role_required("admin")
def nuevo():
    form = ProfesionalForm()
    if form.validate_on_submit():
        profesional = Profesional(
            nombre=form.nombre.data.strip(),
            apellido=form.apellido.data.strip(),
            especialidad=form.especialidad.data.strip() if form.especialidad.data else None,
            telefono=form.telefono.data.strip() if form.telefono.data else None,
            email=form.email.data.strip() if form.email.data else None,
            activo=form.activo.data,
        )
        db.session.add(profesional)
        db.session.commit()
        return redirect(url_for("profesionales.detalle", profesional_id=profesional.id))
    return render_template("profesionales/nuevo.html", form=form)


@profesionales_bp.route("/<int:profesional_id>", methods=["GET"])
@login_required
@role_required("admin")
def detalle(profesional_id):
    profesional = Profesional.query.get_or_404(profesional_id)
    return render_template("profesionales/detalle.html", profesional=profesional)


@profesionales_bp.route("/<int:profesional_id>/editar", methods=["GET", "POST"])
@login_required
@role_required("admin")
def editar(profesional_id):
    profesional = Profesional.query.get_or_404(profesional_id)
    form = ProfesionalForm(obj=profesional)

    if form.validate_on_submit():
        profesional.nombre = form.nombre.data.strip()
        profesional.apellido = form.apellido.data.strip()
        profesional.especialidad = form.especialidad.data.strip() if form.especialidad.data else None
        profesional.telefono = form.telefono.data.strip() if form.telefono.data else None
        profesional.email = form.email.data.strip() if form.email.data else None
        profesional.activo = form.activo.data
        db.session.commit()
        return redirect(url_for("profesionales.detalle", profesional_id=profesional.id))

    return render_template("profesionales/nuevo.html", form=form, profesional=profesional)


@profesionales_bp.route("/htmx/buscar", methods=["GET"])
@login_required
def buscar_htmx():
    q = (request.args.get("q") or "").strip()
    if len(q) < 2:
        return ""

    like = f"%{q}%"
    profesionales = (
        Profesional.query.filter(
            or_(
                Profesional.nombre.ilike(like),
                Profesional.apellido.ilike(like),
                Profesional.especialidad.ilike(like),
            )
        )
        .order_by(Profesional.apellido, Profesional.nombre)
        .limit(10)
        .all()
    )
    rows = [
        f"<li data-id='{p.id}'>{p.apellido}, {p.nombre}</li>" for p in profesionales
    ]
    return "<ul class='search-results'>" + "".join(rows) + "</ul>"
