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
