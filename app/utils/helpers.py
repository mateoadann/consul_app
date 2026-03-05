from datetime import date, datetime, time, timedelta


AGENDA_START_TIME = time(hour=8, minute=0)
AGENDA_END_TIME = time(hour=20, minute=0)


def parse_iso_date(value: str | None, fallback: date | None = None) -> date:
    if not value:
        return fallback or date.today()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return fallback or date.today()


def combine_date_time(base_date: date, base_time: time) -> datetime:
    return datetime.combine(base_date, base_time)


def daterange_slots(
    day: date,
    start_hour: int = 8,
    end_hour: int = 20,
    step_minutes: int = 15,
):
    current = datetime.combine(day, time(hour=start_hour, minute=0))
    finish = datetime.combine(day, time(hour=end_hour, minute=0))

    slots = []
    while current < finish:
        slots.append(current)
        current += timedelta(minutes=step_minutes)
    return slots


def is_15_minute_increment(value: time) -> bool:
    if value is None:
        return False
    return value.minute % 15 == 0 and value.second == 0


def is_time_in_agenda_range(value: time) -> bool:
    if value is None:
        return False
    return AGENDA_START_TIME <= value <= AGENDA_END_TIME


def parse_hhmm(value: str | None) -> time | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return None


def build_time_choices(start: time, end: time, step_minutes: int = 15) -> list[tuple[str, str]]:
    if step_minutes <= 0:
        return []

    current = datetime.combine(date.today(), start)
    finish = datetime.combine(date.today(), end)
    if current > finish:
        return []

    choices = []
    while current <= finish:
        label = current.strftime("%H:%M")
        choices.append((label, label))
        current += timedelta(minutes=step_minutes)
    return choices
