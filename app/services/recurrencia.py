from __future__ import annotations

from datetime import date, datetime, time, timedelta


def generate_weekly_occurrences(
    start_date: date,
    end_date: date,
    every_n_weeks: int,
    patterns: list[dict],
) -> list[dict]:
    if every_n_weeks < 1:
        raise ValueError("every_n_weeks debe ser >= 1")
    if end_date < start_date:
        raise ValueError("end_date no puede ser menor a start_date")

    occurrences: list[dict] = []

    for pattern in patterns:
        weekday = int(pattern["weekday"])
        start_time: time = pattern["start_time"]
        end_time: time = pattern["end_time"]
        consultorio_id = int(pattern["consultorio_id"])

        first_date = start_date + timedelta(days=(weekday - start_date.weekday()) % 7)
        current_date = first_date

        while current_date <= end_date:
            occurrences.append(
                {
                    "start_at": datetime.combine(current_date, start_time),
                    "end_at": datetime.combine(current_date, end_time),
                    "consultorio_id": consultorio_id,
                    "weekday": weekday,
                }
            )
            current_date += timedelta(days=7 * every_n_weeks)

    occurrences.sort(key=lambda item: item["start_at"])
    return occurrences
