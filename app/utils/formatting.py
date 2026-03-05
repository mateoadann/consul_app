from datetime import date, datetime, time

WEEKDAYS_ES = (
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo",
)


def _as_date(value: date | datetime | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    return value


def _as_time(value: time | datetime | None) -> time | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.time()
    return value


def format_fecha_corta(value: date | datetime | None) -> str:
    parsed = _as_date(value)
    if parsed is None:
        return ""
    return parsed.strftime("%d/%m/%y")


def format_hora_24(value: time | datetime | None) -> str:
    parsed = _as_time(value)
    if parsed is None:
        return ""
    return parsed.strftime("%H:%M")


def format_fecha_hora_corta(value: datetime | None) -> str:
    if value is None:
        return ""
    return f"{format_fecha_corta(value)} {format_hora_24(value)}"


def format_fecha_agenda(value: date | datetime | None) -> str:
    parsed = _as_date(value)
    if parsed is None:
        return ""
    weekday = WEEKDAYS_ES[parsed.weekday()].capitalize()
    return f"{weekday} {parsed.day} . {format_fecha_corta(parsed)}"


def format_fecha_agenda_corta(value: date | datetime | None) -> str:
    parsed = _as_date(value)
    if parsed is None:
        return ""

    weekday_map = {
        "lunes": "Lunes",
        "martes": "Martes",
        "miercoles": "Miercoles",
        "jueves": "Jueves",
        "viernes": "Viernes",
        "sabado": "Sabado",
        "domingo": "Domingo",
    }
    weekday = weekday_map[WEEKDAYS_ES[parsed.weekday()]]
    return f"{weekday} {parsed.day}"
