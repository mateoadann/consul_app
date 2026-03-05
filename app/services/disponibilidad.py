from __future__ import annotations

from datetime import date, datetime, timedelta

from psycopg2.extras import DateTimeRange
from sqlalchemy import func, or_

from app.models import Consultorio, Turno
from app.utils.helpers import daterange_slots


def day_bounds(target_date: date) -> tuple[datetime, datetime]:
    start = datetime.combine(target_date, datetime.min.time())
    end = start + timedelta(days=1)
    return start, end


def fetch_turnos_day(target_date: date, profesional_id: int | None = None):
    start, end = day_bounds(target_date)
    day_range = DateTimeRange(start, end, "[)")

    query = (
        Turno.query.join(Turno.paciente)
        .join(Turno.profesional)
        .join(Turno.consultorio)
        .filter(Turno.estado != "cancelado")
        .filter(Turno.durante.op("&&")(day_range))
        .order_by(func.lower(Turno.durante))
    )

    if profesional_id:
        query = query.filter(Turno.profesional_id == profesional_id)

    return query.all()


def fetch_consultorios_activos():
    return Consultorio.query.filter_by(activo=True).order_by(Consultorio.nombre).all()


def build_grid(target_date: date, consultorios, turnos):
    slots = daterange_slots(target_date)

    cell_map: dict[tuple[int, datetime], Turno] = {}
    for turno in turnos:
        for slot in slots:
            if turno.start_at <= slot < turno.end_at:
                cell_map[(turno.consultorio_id, slot)] = turno

    return slots, cell_map


def build_timeline(target_date: date, _consultorios, turnos, consultorio_id: int | None = None):
    """Construye datos para la vista timeline vertical."""
    slots = daterange_slots(target_date, step_minutes=30)
    result: list[dict] = []

    if consultorio_id:
        turnos_consultorio = [t for t in turnos if t.consultorio_id == consultorio_id]
        turno_map = {t.start_at: t for t in turnos_consultorio}
        covered: set[datetime] = set()

        for slot in slots:
            if slot in covered:
                continue

            turno = turno_map.get(slot)
            if not turno:
                mid_slot = slot + timedelta(minutes=15)
                turno = turno_map.get(mid_slot)

            if not turno:
                covering = next(
                    (
                        t
                        for t in turnos_consultorio
                        if t.start_at < slot < t.end_at
                    ),
                    None,
                )
                if covering:
                    covered.add(slot)
                    continue

            result.append({"time": slot, "turnos": [turno] if turno else []})

            if turno:
                continuation = slot + timedelta(minutes=30)
                while continuation < turno.end_at:
                    covered.add(continuation)
                    continuation += timedelta(minutes=30)
    else:
        slot_turnos: dict[datetime, list] = {}
        for turno in turnos:
            rounded = turno.start_at.replace(
                minute=(turno.start_at.minute // 30) * 30,
                second=0,
                microsecond=0,
            )
            slot_turnos.setdefault(rounded, []).append(turno)

        for slot in slots:
            result.append({"time": slot, "turnos": slot_turnos.get(slot, [])})

    return result


def find_conflicts(
    start_at: datetime,
    end_at: datetime,
    consultorio_id: int,
    profesional_id: int,
    paciente_id: int,
    exclude_turno_id: int | None = None,
):
    requested_range = DateTimeRange(start_at, end_at, "[)")

    query = (
        Turno.query.filter(Turno.estado != "cancelado")
        .filter(Turno.durante.op("&&")(requested_range))
        .filter(
            or_(
                Turno.consultorio_id == consultorio_id,
                Turno.profesional_id == profesional_id,
                Turno.paciente_id == paciente_id,
            )
        )
    )

    if exclude_turno_id is not None:
        query = query.filter(Turno.id != exclude_turno_id)

    return query.order_by(func.lower(Turno.durante)).all()


def suggest_alternatives(
    start_at: datetime,
    duration_minutes: int,
    consultorio_id: int,
    profesional_id: int,
    paciente_id: int,
    exclude_turno_id: int | None = None,
    limit: int = 4,
):
    suggestions = []
    increments = [15, 30, 45, 60, -15, -30, -45, -60]

    for minutes in increments:
        candidate_start = start_at + timedelta(minutes=minutes)
        candidate_end = candidate_start + timedelta(minutes=duration_minutes)

        same_day = candidate_start.date() == start_at.date() and candidate_end.date() == start_at.date()
        if not same_day:
            continue

        conflicts = find_conflicts(
            candidate_start,
            candidate_end,
            consultorio_id=consultorio_id,
            profesional_id=profesional_id,
            paciente_id=paciente_id,
            exclude_turno_id=exclude_turno_id,
        )
        if conflicts:
            continue

        suggestions.append((candidate_start, candidate_end))
        if len(suggestions) >= limit:
            break

    suggestions.sort(key=lambda item: item[0])
    return suggestions
