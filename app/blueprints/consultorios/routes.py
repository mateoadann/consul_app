from flask import Blueprint, redirect, render_template, url_for
from flask_login import login_required

from app.extensions import db
from app.models import Consultorio
from app.utils.decorators import role_required

from .forms import ConsultorioForm


consultorios_bp = Blueprint("consultorios", __name__, url_prefix="/consultorios")


@consultorios_bp.route("", methods=["GET"])
@login_required
@role_required("admin")
def lista():
    consultorios = Consultorio.query.order_by(Consultorio.nombre).all()
    form = ConsultorioForm()
    if not form.color.data:
        form.color.data = "#EA8711"
    return render_template("consultorios/lista.html", consultorios=consultorios, form=form)


@consultorios_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@role_required("admin")
def nuevo():
    form = ConsultorioForm()

    if form.validate_on_submit():
        existing = Consultorio.query.filter_by(nombre=form.nombre.data.strip()).first()
        if existing:
            form.nombre.errors.append("Ya existe un consultorio con ese nombre.")
            return (
                render_template(
                    "consultorios/lista.html",
                    form=form,
                    consultorios=Consultorio.query.order_by(Consultorio.nombre).all(),
                ),
                422,
            )

        consultorio = Consultorio(
            nombre=form.nombre.data.strip(),
            color=form.color.data,
            activo=form.activo.data,
        )
        db.session.add(consultorio)
        db.session.commit()
        return redirect(url_for("consultorios.lista"))

    return render_template("consultorios/lista.html", form=form, consultorios=Consultorio.query.all())


@consultorios_bp.route("/<int:consultorio_id>/editar", methods=["GET", "POST"])
@login_required
@role_required("admin")
def editar(consultorio_id):
    consultorio = Consultorio.query.get_or_404(consultorio_id)
    form = ConsultorioForm(obj=consultorio)

    if form.validate_on_submit():
        existing = (
            Consultorio.query.filter(
                Consultorio.nombre == form.nombre.data.strip(),
                Consultorio.id != consultorio.id,
            )
            .limit(1)
            .first()
        )
        if existing:
            form.nombre.errors.append("Ya existe un consultorio con ese nombre.")
            consultorios = Consultorio.query.order_by(Consultorio.nombre).all()
            return render_template(
                "consultorios/lista.html",
                form=form,
                consultorios=consultorios,
                consultorio_edit=consultorio,
            ), 422

        consultorio.nombre = form.nombre.data.strip()
        consultorio.color = form.color.data
        consultorio.activo = form.activo.data
        db.session.commit()
        return redirect(url_for("consultorios.lista"))

    consultorios = Consultorio.query.order_by(Consultorio.nombre).all()
    return render_template(
        "consultorios/lista.html",
        form=form,
        consultorios=consultorios,
        consultorio_edit=consultorio,
    )
