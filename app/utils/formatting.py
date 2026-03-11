from datetime import date, datetime, time

MONTHS_ES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

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


def format_fecha_larga(value: date | datetime | None) -> str:
    parsed = _as_date(value)
    if parsed is None:
        return ""
    month = MONTHS_ES[parsed.month - 1]
    return f"{parsed.day} de {month} de {parsed.year}"


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


FORMATO_NOMBRE_OPTIONS = {
    "nombre": "Nombre",
    "nombre_apellido": "Nombre Apellido",
    "nombre_inicial": "Nombre + inicial",
    "apodo": "Apodo",
    "apodo_inicial": "Apodo + inicial",
}

FORMATO_NOMBRE_DEFAULT = "nombre_inicial"


def format_display_name(entity, format_key: str) -> str:
    nombre = getattr(entity, "nombre", "")
    apellido = getattr(entity, "apellido", "")
    apodo = getattr(entity, "apodo", None) or ""
    inicial = f"{apellido[0]}." if apellido else ""

    fallback = f"{nombre} {inicial}".strip()

    if format_key == "nombre":
        return nombre
    elif format_key == "nombre_apellido":
        return f"{nombre} {apellido}".strip()
    elif format_key == "nombre_inicial":
        return fallback
    elif format_key == "apodo":
        return apodo if apodo else fallback
    elif format_key == "apodo_inicial":
        if apodo:
            return f"{apodo} {inicial}".strip()
        return fallback

    return fallback
