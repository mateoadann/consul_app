from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from app.models import Profesional
from app.services.disponibilidad import (
    build_grid,
    build_timeline,
    fetch_consultorios_activos,
    fetch_turnos_day,
)
from app.utils.helpers import parse_iso_date


agenda_bp = Blueprint("agenda", __name__)


def _resolve_profesional_id_filter(mis_turnos: bool, profesional_id_raw: str | None):
    if mis_turnos and current_user.profesional:
        return current_user.profesional.id

    if not profesional_id_raw:
        return None

    try:
        return int(profesional_id_raw)
    except ValueError:
        return None


def _build_agenda_context(
    target_date: date,
    mis_turnos: bool,
    profesional_id_raw: str | None,
    consultorio_id_filter: int | None = None,
):
    consultorios = fetch_consultorios_activos()
    profesional_filter = _resolve_profesional_id_filter(mis_turnos, profesional_id_raw)
    turnos = fetch_turnos_day(target_date, profesional_filter)
    slots, cell_map = build_grid(target_date, consultorios, turnos)
    timeline = build_timeline(target_date, consultorios, turnos, consultorio_id_filter)

    profesionales = Profesional.query.filter_by(activo=True).order_by(Profesional.apellido).all()

    return {
        "fecha": target_date,
        "hoy": date.today(),
        "fecha_prev": target_date - timedelta(days=1),
        "fecha_next": target_date + timedelta(days=1),
        "consultorios": consultorios,
        "turnos": turnos,
        "slots": slots,
        "cell_map": cell_map,
        "timeline": timeline,
        "consultorio_id_filter": consultorio_id_filter,
        "mis_turnos": mis_turnos,
        "profesionales": profesionales,
        "profesional_id_filter": profesional_filter,
        "profesional_id_raw": profesional_id_raw,
    }


@agenda_bp.route("/", methods=["GET"])
@login_required
def index():
    target_date = parse_iso_date(request.args.get("fecha"), fallback=date.today())
    mis_turnos = request.args.get("mine") == "1"
    consultorio_id_filter = request.args.get("consultorio_id", type=int)
    context = _build_agenda_context(
        target_date,
        mis_turnos,
        request.args.get("profesional_id"),
        consultorio_id_filter,
    )
    return render_template("agenda/index.html", **context)


@agenda_bp.route("/dia/<fecha>", methods=["GET"])
@login_required
def day(fecha):
    try:
        target_date = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        target_date = date.today()
    mis_turnos = request.args.get("mine") == "1"
    consultorio_id_filter = request.args.get("consultorio_id", type=int)
    context = _build_agenda_context(
        target_date,
        mis_turnos,
        request.args.get("profesional_id"),
        consultorio_id_filter,
    )
    return render_template("agenda/index.html", **context)


@agenda_bp.route("/htmx/grilla", methods=["GET"])
@login_required
def htmx_grilla():
    target_date = parse_iso_date(request.args.get("fecha"), fallback=date.today())
    mis_turnos = request.args.get("mine") == "1"
    consultorio_id_filter = request.args.get("consultorio_id", type=int)
    context = _build_agenda_context(
        target_date,
        mis_turnos,
        request.args.get("profesional_id"),
        consultorio_id_filter,
    )
    return render_template("agenda/_grilla_combined.html", **context)
