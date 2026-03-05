from datetime import date, datetime

from psycopg2.extras import DateTimeRange

from app.models import Turno
from app.services.disponibilidad import build_grid


class DummyConsultorio:
    def __init__(self, consultorio_id):
        self.id = consultorio_id


def test_build_grid_marks_occupied_slots():
    target_date = date.today()
    consultorios = [DummyConsultorio(1)]

    start = datetime.combine(target_date, datetime.strptime("09:00", "%H:%M").time())
    end = datetime.combine(target_date, datetime.strptime("09:30", "%H:%M").time())

    turno = Turno(consultorio_id=1, durante=DateTimeRange(start, end, "[)"))
    slots, cell_map = build_grid(target_date, consultorios, [turno])

    assert any(slot.strftime("%H:%M") == "09:00" for slot in slots)
    slot_9 = [slot for slot in slots if slot.strftime("%H:%M") == "09:00"][0]
    assert cell_map[(1, slot_9)] == turno
