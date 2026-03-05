from datetime import date, datetime, time, timedelta

import pytest
from psycopg2.extras import DateTimeRange
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Consultorio, Paciente, Profesional, Turno, User


def test_state_transition_rules():
    turno = Turno(estado="reservado")
    assert turno.can_transition_to("confirmado") is True
    assert turno.can_transition_to("cancelado") is True
    assert turno.can_transition_to("atendido") is False


@pytest.mark.postgres
def test_no_overlap_same_consultorio(client):
    user = User(username="u1", role="admin", nombre="Admin", activo=True)
    user.set_password("x")
    db.session.add(user)

    profesional = Profesional(nombre="Ana", apellido="Medica", activo=True)
    consultorio = Consultorio(nombre="Consultorio A", activo=True)
    paciente_a = Paciente(nombre="A", apellido="Uno", dni="100", activo=True)
    paciente_b = Paciente(nombre="B", apellido="Dos", dni="101", activo=True)
    db.session.add_all([profesional, consultorio, paciente_a, paciente_b])
    db.session.commit()

    day = date.today()
    start = datetime.combine(day, time(9, 0))
    end = start + timedelta(minutes=30)

    t1 = Turno(
        paciente_id=paciente_a.id,
        profesional_id=profesional.id,
        consultorio_id=consultorio.id,
        durante=DateTimeRange(start, end, "[)"),
        estado="reservado",
        created_by=user.id,
    )
    db.session.add(t1)
    db.session.commit()

    t2 = Turno(
        paciente_id=paciente_b.id,
        profesional_id=profesional.id,
        consultorio_id=consultorio.id,
        durante=DateTimeRange(start, end, "[)"),
        estado="reservado",
        created_by=user.id,
    )
    db.session.add(t2)

    with pytest.raises(IntegrityError):
        db.session.commit()
