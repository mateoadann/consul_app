import json
import uuid
from datetime import date, datetime, timedelta

from psycopg2.extras import DateTimeRange
from sqlalchemy.exc import IntegrityError

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Consultorio, Paciente, Profesional, Turno, TurnoSerieLog
from app.services.disponibilidad import fetch_turnos_day, find_conflicts, suggest_alternatives
from app.services.recurrencia import generate_weekly_occurrences
from app.utils.helpers import (
    AGENDA_END_TIME,
    is_15_minute_increment,
    is_time_in_agenda_range,
    parse_hhmm,
    parse_iso_date,
)

from .forms import EstadoTurnoForm, TurnoForm


turnos_bp = Blueprint("turnos", __name__, url_prefix="/turnos")


def _populate_turno_choices(form: TurnoForm):
    form.consultorio_id.choices = [
        (c.id, c.nombre)
        for c in Consultorio.query.filter_by(activo=True).order_by(Consultorio.nombre).all()
    ]
    form.profesional_id.choices = [
        (p.id, f"Dr./Dra. {p.apellido}, {p.nombre}")
        for p in Profesional.query.filter_by(activo=True).order_by(Profesional.apellido, Profesional.nombre).all()
    ]


def _default_profesional_id():
    if current_user.is_authenticated and current_user.profesional:
        return current_user.profesional.id
    return None


def _parse_datetime(form: TurnoForm):
    start_time = parse_hhmm(form.hora_inicio.data)
    end_time = parse_hhmm(form.hora_fin.data)
    if not form.fecha.data or not start_time or not end_time:
        raise ValueError("Fecha u horario invalido.")

    start_at = datetime.combine(form.fecha.data, start_time)
    end_at = datetime.combine(form.fecha.data, end_time)
    return start_at, end_at


def _duration_minutes(start_at: datetime, end_at: datetime) -> int:
    return int((end_at - start_at).total_seconds() / 60)


def _fill_form_from_turno(form: TurnoForm, turno: Turno):
    form.fecha.data = turno.start_at.date()
    form.hora_inicio.data = turno.start_at.strftime("%H:%M")
    form.hora_fin.data = turno.end_at.strftime("%H:%M")
    form.consultorio_id.data = turno.consultorio_id
    form.profesional_id.data = turno.profesional_id
    form.paciente_id.data = str(turno.paciente_id)
    form.paciente_query.data = (
        f"{turno.paciente.apellido}, {turno.paciente.nombre} - DNI {turno.paciente.dni}"
    )


def _assign_turno_from_form(turno: Turno, form: TurnoForm, paciente_id: int, start_at, end_at):
    turno.paciente_id = paciente_id
    turno.profesional_id = form.profesional_id.data
    turno.consultorio_id = form.consultorio_id.data
    turno.durante = DateTimeRange(start_at, end_at, "[)")


def _is_conflict_error(exc: IntegrityError) -> bool:
    return getattr(exc.orig, "pgcode", None) == "23P01"


def _build_fallback_pattern_from_form(form: TurnoForm) -> dict:
    start_time = parse_hhmm(form.hora_inicio.data)
    end_time = parse_hhmm(form.hora_fin.data)

    return {
        "weekday": form.fecha.data.weekday(),
        "start_time": start_time,
        "end_time": end_time,
        "consultorio_id": form.consultorio_id.data,
        "start_label": form.hora_inicio.data,
        "end_label": form.hora_fin.data,
    }


def _parse_recurrencia_patrones(raw_value: str | None, fallback_pattern: dict):
    if not raw_value:
        return [fallback_pattern]

    try:
        data = json.loads(raw_value)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, list) or not data:
        return None

    patterns = []
    for item in data:
        if not isinstance(item, dict):
            return None

        try:
            weekday = int(item.get("weekday"))
            consultorio_id = int(item.get("consultorio_id"))
            start_time = datetime.strptime(item.get("hora_inicio", ""), "%H:%M").time()
            end_time = datetime.strptime(item.get("hora_fin", ""), "%H:%M").time()
        except (TypeError, ValueError):
            return None

        if weekday < 0 or weekday > 6:
            return None
        if not is_15_minute_increment(start_time) or not is_15_minute_increment(end_time):
            return None
        if not is_time_in_agenda_range(start_time) or not is_time_in_agenda_range(end_time):
            return None
        if end_time <= start_time:
            return None

        patterns.append(
            {
                "weekday": weekday,
                "start_time": start_time,
                "end_time": end_time,
                "consultorio_id": consultorio_id,
                "start_label": start_time.strftime("%H:%M"),
                "end_label": end_time.strftime("%H:%M"),
            }
        )

    return patterns


def _build_conflict_reason(conflicts, consultorio_id: int, profesional_id: int, paciente_id: int) -> str:
    reasons = []
    if any(t.consultorio_id == consultorio_id for t in conflicts):
        reasons.append("consultorio ocupado")
    if any(t.profesional_id == profesional_id for t in conflicts):
        reasons.append("profesional ocupado")
    if any(t.paciente_id == paciente_id for t in conflicts):
        reasons.append("paciente con otro turno")
    if not reasons:
        reasons.append("solapamiento")
    return ", ".join(reasons)


def _validate_recurrencia(form: TurnoForm):
    if not form.fecha_limite.data:
        form.fecha_limite.errors.append("Defini una fecha limite para la serie.")
        return None

    if form.fecha_limite.data < form.fecha.data:
        form.fecha_limite.errors.append("La fecha limite no puede ser menor a la fecha inicial.")
        return None

    cada_n = form.cada_n_semanas.data or 1
    if cada_n < 1:
        form.cada_n_semanas.errors.append("El intervalo debe ser de al menos 1 semana.")
        return None

    fallback = _build_fallback_pattern_from_form(form)
    patterns = _parse_recurrencia_patrones(form.recurrencia_patrones.data, fallback)
    if not patterns:
        form.recurrencia_patrones.errors.append(
            "No se pudieron leer los patrones. Revisa dias/horarios/consultorios."
        )
        return None

    try:
        occurrences = generate_weekly_occurrences(
            start_date=form.fecha.data,
            end_date=form.fecha_limite.data,
            every_n_weeks=cada_n,
            patterns=patterns,
        )
    except ValueError:
        form.recurrencia_patrones.errors.append("La configuracion de repeticion es invalida.")
        return None

    if not occurrences:
        form.recurrencia_patrones.errors.append("No se generaron ocurrencias con esos patrones.")
        return None

    if len(occurrences) > 260:
        form.fecha_limite.errors.append("La serie es demasiado grande (maximo 260 ocurrencias).")
        return None

    return {"occurrences": occurrences, "patterns": patterns, "cada_n": cada_n}


def _create_recurrent_turnos(form: TurnoForm, paciente_id: int, paciente: Paciente):
    recurrence_data = _validate_recurrencia(form)
    if not recurrence_data:
        return None

    occurrences = recurrence_data["occurrences"]
    patterns = recurrence_data["patterns"]
    serie_id = str(uuid.uuid4())

    created = 0
    failed: list[dict] = []

    for occurrence in occurrences:
        start_at = occurrence["start_at"]
        end_at = occurrence["end_at"]
        consultorio_id = occurrence["consultorio_id"]

        conflicts = find_conflicts(
            start_at,
            end_at,
            consultorio_id=consultorio_id,
            profesional_id=form.profesional_id.data,
            paciente_id=paciente_id,
        )
        if conflicts:
            failed.append(
                {
                    "fecha": start_at.date().isoformat(),
                    "inicio": start_at.strftime("%H:%M"),
                    "fin": end_at.strftime("%H:%M"),
                    "consultorio_id": consultorio_id,
                    "motivo": _build_conflict_reason(
                        conflicts,
                        consultorio_id=consultorio_id,
                        profesional_id=form.profesional_id.data,
                        paciente_id=paciente_id,
                    ),
                }
            )
            continue

        turno = Turno(
            paciente_id=paciente_id,
            profesional_id=form.profesional_id.data,
            consultorio_id=consultorio_id,
            durante=DateTimeRange(start_at, end_at, "[)"),
            estado="reservado",
            created_by=current_user.id,
        )
        db.session.add(turno)

        try:
            db.session.commit()
            created += 1
        except IntegrityError as exc:
            db.session.rollback()
            if _is_conflict_error(exc):
                failed.append(
                    {
                        "fecha": start_at.date().isoformat(),
                        "inicio": start_at.strftime("%H:%M"),
                        "fin": end_at.strftime("%H:%M"),
                        "consultorio_id": consultorio_id,
                        "motivo": "ocupado por otra reserva simultanea",
                    }
                )
                continue
            raise

    log = TurnoSerieLog(
        serie_id=serie_id,
        user_id=current_user.id,
        paciente_id=paciente.id,
        profesional_id=form.profesional_id.data,
        fecha_inicio=form.fecha.data,
        fecha_limite=form.fecha_limite.data,
        cada_n_semanas=recurrence_data["cada_n"],
        patrones_json=[
            {
                "weekday": p["weekday"],
                "hora_inicio": p["start_label"],
                "hora_fin": p["end_label"],
                "consultorio_id": p["consultorio_id"],
            }
            for p in patterns
        ],
        total_intentados=len(occurrences),
        total_creados=created,
        total_fallidos=len(failed),
        fallidos_json=failed or None,
    )
    db.session.add(log)
    db.session.commit()

    return {
        "created": created,
        "failed": failed,
        "attempted": len(occurrences),
    }


@turnos_bp.route("/htmx/ocupados", methods=["GET"])
@login_required
def htmx_ocupados():
    """Retorna los horarios ocupados de un consultorio en una fecha."""
    fecha = parse_iso_date(request.args.get("fecha"), fallback=date.today())
    consultorio_id = request.args.get("consultorio_id", type=int)

    if not consultorio_id:
        return ""

    turnos = fetch_turnos_day(fecha)
    ocupados = [turno for turno in turnos if turno.consultorio_id == consultorio_id]

    return render_template("turnos/_ocupados.html", ocupados=ocupados, fecha=fecha)


@turnos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    form = TurnoForm()
    _populate_turno_choices(form)

    if request.method == "GET":
        fecha = request.args.get("fecha")
        hora = request.args.get("hora")
        consultorio_id = request.args.get("consultorio_id")

        form.fecha.data = date.today()
        form.hora_inicio.data = "09:00"
        form.hora_fin.data = "09:30"
        form.cada_n_semanas.data = 1

        if fecha:
            try:
                form.fecha.data = datetime.strptime(fecha, "%Y-%m-%d").date()
            except ValueError:
                pass
        if hora:
            selected = parse_hhmm(hora)
            if selected and is_15_minute_increment(selected) and selected < AGENDA_END_TIME:
                form.hora_inicio.data = selected.strftime("%H:%M")
                end_candidate = (
                    datetime.combine(date.today(), selected) + timedelta(minutes=30)
                ).time()
                form.hora_fin.data = min(end_candidate, AGENDA_END_TIME).strftime("%H:%M")
        if consultorio_id and consultorio_id.isdigit():
            form.consultorio_id.data = int(consultorio_id)

        default_prof = _default_profesional_id()
        if default_prof:
            form.profesional_id.data = default_prof

        return render_template(
            "turnos/nuevo.html",
            form=form,
            alternatives=[],
            is_edit=False,
            allow_recurrencia=True,
        )

    alternatives = []
    if form.validate_on_submit():
        try:
            paciente_id = int(form.paciente_id.data)
        except (TypeError, ValueError):
            form.paciente_query.errors.append("Selecciona un paciente valido.")
            return render_template(
                "turnos/nuevo.html",
                form=form,
                alternatives=alternatives,
                is_edit=False,
                allow_recurrencia=True,
            ), 422

        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            form.paciente_query.errors.append("Selecciona un paciente existente.")
            return render_template(
                "turnos/nuevo.html",
                form=form,
                alternatives=alternatives,
                is_edit=False,
                allow_recurrencia=True,
            ), 422

        if form.repetir.data:
            recurring_result = _create_recurrent_turnos(form, paciente_id=paciente_id, paciente=paciente)
            if not recurring_result:
                return render_template(
                    "turnos/nuevo.html",
                    form=form,
                    alternatives=alternatives,
                    is_edit=False,
                    allow_recurrencia=True,
                ), 422

            if recurring_result["created"] == 0:
                flash(
                    f"No se pudo crear la serie. {recurring_result['attempted']} intentos, 0 creados.",
                    "error",
                )
                return render_template(
                    "turnos/nuevo.html",
                    form=form,
                    alternatives=alternatives,
                    is_edit=False,
                    allow_recurrencia=True,
                ), 422

            if recurring_result["failed"]:
                flash(
                    (
                        f"Serie creada parcialmente: {recurring_result['created']} creados, "
                        f"{len(recurring_result['failed'])} no se pudieron crear."
                    ),
                    "error",
                )
            else:
                flash(
                    f"Serie creada correctamente ({recurring_result['created']} turnos).",
                    "success",
                )
            return redirect(url_for("agenda.index", fecha=form.fecha.data.isoformat()))

        start_at, end_at = _parse_datetime(form)
        duration_minutes = _duration_minutes(start_at, end_at)

        conflicts = find_conflicts(
            start_at,
            end_at,
            consultorio_id=form.consultorio_id.data,
            profesional_id=form.profesional_id.data,
            paciente_id=paciente_id,
        )
        if conflicts:
            first = conflicts[0]
            form.hora_inicio.errors.append(
                f"Este horario ya fue ocupado por {first.paciente.nombre_completo}."
            )
            alternatives = suggest_alternatives(
                start_at,
                duration_minutes,
                consultorio_id=form.consultorio_id.data,
                profesional_id=form.profesional_id.data,
                paciente_id=paciente_id,
            )
            return render_template(
                "turnos/nuevo.html",
                form=form,
                alternatives=alternatives,
                is_edit=False,
                allow_recurrencia=True,
            ), 422

        turno = Turno(
            paciente_id=paciente_id,
            profesional_id=form.profesional_id.data,
            consultorio_id=form.consultorio_id.data,
            durante=DateTimeRange(start_at, end_at, "[)"),
            estado="reservado",
            created_by=current_user.id,
        )
        db.session.add(turno)

        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            if _is_conflict_error(exc):
                form.hora_inicio.errors.append("Ese horario se acaba de ocupar. Elegi otro horario.")
                alternatives = suggest_alternatives(
                    start_at,
                    duration_minutes,
                    consultorio_id=form.consultorio_id.data,
                    profesional_id=form.profesional_id.data,
                    paciente_id=paciente_id,
                )
                return render_template(
                    "turnos/nuevo.html",
                    form=form,
                    alternatives=alternatives,
                    is_edit=False,
                    allow_recurrencia=True,
                ), 422
            raise

        flash("Turno reservado correctamente.", "success")
        return redirect(url_for("agenda.index", fecha=form.fecha.data.isoformat()))

    return render_template(
        "turnos/nuevo.html",
        form=form,
        alternatives=alternatives,
        is_edit=False,
        allow_recurrencia=True,
    ), 422


@turnos_bp.route("/<int:turno_id>/editar", methods=["GET", "POST"])
@login_required
def editar(turno_id):
    turno = Turno.query.get_or_404(turno_id)
    if turno.estado in {"atendido", "cancelado"}:
        flash("No se puede editar un turno finalizado.", "error")
        return redirect(url_for("turnos.detalle", turno_id=turno.id))

    form = TurnoForm()
    _populate_turno_choices(form)

    if request.method == "GET":
        _fill_form_from_turno(form, turno)
        return render_template(
            "turnos/nuevo.html",
            form=form,
            alternatives=[],
            is_edit=True,
            turno=turno,
            allow_recurrencia=False,
        )

    alternatives = []
    if form.validate_on_submit():
        if form.repetir.data:
            form.repetir.errors.append("La recurrencia solo se define al crear una serie nueva.")
            return (
                render_template(
                    "turnos/nuevo.html",
                    form=form,
                    alternatives=alternatives,
                    is_edit=True,
                    turno=turno,
                    allow_recurrencia=False,
                ),
                422,
            )

        try:
            paciente_id = int(form.paciente_id.data)
        except (TypeError, ValueError):
            form.paciente_query.errors.append("Selecciona un paciente valido.")
            return (
                render_template(
                    "turnos/nuevo.html",
                    form=form,
                    alternatives=alternatives,
                    is_edit=True,
                    turno=turno,
                    allow_recurrencia=False,
                ),
                422,
            )

        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            form.paciente_query.errors.append("Selecciona un paciente existente.")
            return (
                render_template(
                    "turnos/nuevo.html",
                    form=form,
                    alternatives=alternatives,
                    is_edit=True,
                    turno=turno,
                    allow_recurrencia=False,
                ),
                422,
            )

        start_at, end_at = _parse_datetime(form)
        duration_minutes = _duration_minutes(start_at, end_at)

        conflicts = find_conflicts(
            start_at,
            end_at,
            consultorio_id=form.consultorio_id.data,
            profesional_id=form.profesional_id.data,
            paciente_id=paciente_id,
            exclude_turno_id=turno.id,
        )
        if conflicts:
            first = conflicts[0]
            form.hora_inicio.errors.append(
                f"Este horario ya fue ocupado por {first.paciente.nombre_completo}."
            )
            alternatives = suggest_alternatives(
                start_at,
                duration_minutes,
                consultorio_id=form.consultorio_id.data,
                profesional_id=form.profesional_id.data,
                paciente_id=paciente_id,
                exclude_turno_id=turno.id,
            )
            return (
                render_template(
                    "turnos/nuevo.html",
                    form=form,
                    alternatives=alternatives,
                    is_edit=True,
                    turno=turno,
                    allow_recurrencia=False,
                ),
                422,
            )

        _assign_turno_from_form(turno, form, paciente_id, start_at, end_at)

        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            if _is_conflict_error(exc):
                form.hora_inicio.errors.append("Ese horario se acaba de ocupar. Elegi otro horario.")
                alternatives = suggest_alternatives(
                    start_at,
                    duration_minutes,
                    consultorio_id=form.consultorio_id.data,
                    profesional_id=form.profesional_id.data,
                    paciente_id=paciente_id,
                    exclude_turno_id=turno.id,
                )
                return (
                    render_template(
                        "turnos/nuevo.html",
                        form=form,
                        alternatives=alternatives,
                        is_edit=True,
                        turno=turno,
                        allow_recurrencia=False,
                    ),
                    422,
                )
            raise

        flash("Turno actualizado.", "success")
        return redirect(url_for("turnos.detalle", turno_id=turno.id))

    return (
        render_template(
            "turnos/nuevo.html",
            form=form,
            alternatives=alternatives,
            is_edit=True,
            turno=turno,
            allow_recurrencia=False,
        ),
        422,
    )


@turnos_bp.route("/<int:turno_id>", methods=["GET"])
@login_required
def detalle(turno_id):
    turno = Turno.query.get_or_404(turno_id)
    form_estado = EstadoTurnoForm()
    return render_template("turnos/detalle.html", turno=turno, form_estado=form_estado)


@turnos_bp.route("/<int:turno_id>/estado", methods=["POST"])
@login_required
def cambiar_estado(turno_id):
    turno = Turno.query.get_or_404(turno_id)
    form = EstadoTurnoForm()

    if not form.validate_on_submit():
        flash("No se pudo actualizar el estado.", "error")
        return redirect(url_for("turnos.detalle", turno_id=turno_id))

    nuevo_estado = form.estado.data
    motivo = form.motivo_cancelacion.data.strip() if form.motivo_cancelacion.data else None

    try:
        turno.apply_state(nuevo_estado, actor_user_id=current_user.id, motivo=motivo)
    except ValueError:
        flash("Transicion de estado invalida.", "error")
        return redirect(url_for("turnos.detalle", turno_id=turno_id))

    db.session.commit()
    flash("Estado actualizado.", "success")
    return redirect(url_for("turnos.detalle", turno_id=turno_id))


@turnos_bp.route("/<int:turno_id>/confirmar-cancelacion", methods=["GET"])
@login_required
def confirmar_cancelacion(turno_id):
    turno = Turno.query.get_or_404(turno_id)
    return render_template("turnos/_confirm_cancel.html", turno=turno)
