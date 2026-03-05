from datetime import date, time

from app.services.recurrencia import generate_weekly_occurrences


def test_generate_weekly_occurrences_multiple_patterns_same_series():
    start_date = date(2026, 2, 1)
    end_date = date(2026, 2, 15)

    patterns = [
        {
            "weekday": 0,
            "start_time": time(16, 0),
            "end_time": time(17, 0),
            "consultorio_id": 1,
        },
        {
            "weekday": 3,
            "start_time": time(15, 0),
            "end_time": time(16, 0),
            "consultorio_id": 3,
        },
    ]

    occurrences = generate_weekly_occurrences(
        start_date=start_date,
        end_date=end_date,
        every_n_weeks=1,
        patterns=patterns,
    )

    assert len(occurrences) == 4
    assert occurrences[0]["start_at"].strftime("%Y-%m-%d %H:%M") == "2026-02-02 16:00"
    assert occurrences[1]["start_at"].strftime("%Y-%m-%d %H:%M") == "2026-02-05 15:00"
    assert occurrences[2]["start_at"].strftime("%Y-%m-%d %H:%M") == "2026-02-09 16:00"
    assert occurrences[3]["start_at"].strftime("%Y-%m-%d %H:%M") == "2026-02-12 15:00"


def test_generate_weekly_occurrences_every_two_weeks():
    start_date = date(2026, 2, 1)
    end_date = date(2026, 2, 28)

    patterns = [
        {
            "weekday": 0,
            "start_time": time(16, 0),
            "end_time": time(17, 0),
            "consultorio_id": 1,
        }
    ]

    occurrences = generate_weekly_occurrences(
        start_date=start_date,
        end_date=end_date,
        every_n_weeks=2,
        patterns=patterns,
    )

    assert [o["start_at"].strftime("%Y-%m-%d") for o in occurrences] == [
        "2026-02-02",
        "2026-02-16",
    ]
