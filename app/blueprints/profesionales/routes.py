from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import or_

from app.models import Profesional
from app.utils.decorators import role_required


profesionales_bp = Blueprint("profesionales", __name__, url_prefix="/profesionales")


@profesionales_bp.route("", methods=["GET"])
@login_required
@role_required("admin")
def lista():
    """Lista de profesionales (solo lectura, gestion via admin/usuarios)."""
    profesionales = Profesional.query.order_by(Profesional.apellido, Profesional.nombre).all()
    return render_template("profesionales/lista.html", profesionales=profesionales)


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
