from __future__ import annotations

import calendar
import json
from datetime import date, timedelta

from flask import current_app
from pywebpush import WebPushException, webpush
from sqlalchemy import extract

from app.extensions import db
from app.models import NotificationLog, Paciente, PushSubscription

INTERVALS = {
    5: "5_days",
    1: "1_day",
    0: "today",
}

MESSAGES = {
    "5_days": "🎂 En 5 días es el cumpleaños de {nombre}",
    "1_day": "🎂 Mañana es el cumpleaños de {nombre}",
    "today": "🎂 ¡Hoy es el cumpleaños de {nombre}!",
}


def get_upcoming_birthdays(days_ahead: int) -> list[Paciente]:
    """Query patients whose birthday matches target date.

    Uses EXTRACT(MONTH/DAY) on PostgreSQL.
    Feb 29 edge case: in non-leap years, Feb 29 birthdays match on Feb 28.
    """
    target = date.today() + timedelta(days=days_ahead)
    target_month = target.month
    target_day = target.day

    query = Paciente.query.filter(
        Paciente.cumpleanos.isnot(None),
        Paciente.activo == True,  # noqa: E712
        extract("month", Paciente.cumpleanos) == target_month,
        extract("day", Paciente.cumpleanos) == target_day,
    )

    patients = query.all()

    # Feb 29 edge case: if target is Feb 28 and NOT a leap year,
    # also include patients born on Feb 29
    if target_month == 2 and target_day == 28 and not calendar.isleap(target.year):
        feb29_patients = Paciente.query.filter(
            Paciente.cumpleanos.isnot(None),
            Paciente.activo == True,  # noqa: E712
            extract("month", Paciente.cumpleanos) == 2,
            extract("day", Paciente.cumpleanos) == 29,
        ).all()
        patients.extend(feb29_patients)

    return patients


def build_notification_payload(paciente: Paciente, interval_key: str) -> dict:
    """Build the push notification payload JSON."""
    nombre = f"{paciente.nombre} {paciente.apellido}"
    return {
        "title": "ConsulApp",
        "body": MESSAGES[interval_key].format(nombre=nombre),
        "url": f"/pacientes/{paciente.id}",
        "tag": f"birthday-{paciente.id}-{interval_key}",
    }


def send_push(subscription: PushSubscription, payload: dict) -> bool:
    """Send a single push notification. Returns True if successful.

    Handles 410 Gone by deleting the stale subscription.
    """
    try:
        webpush(
            subscription_info=subscription.to_push_info(),
            data=json.dumps(payload),
            vapid_private_key=current_app.config["VAPID_PRIVATE_KEY"],
            vapid_claims={"sub": current_app.config["VAPID_SUBJECT"]},
        )
        return True
    except WebPushException as e:
        if e.response and e.response.status_code in (404, 410):
            db.session.delete(subscription)
            db.session.commit()
            current_app.logger.info(f"Removed stale subscription {subscription.id}")
        else:
            current_app.logger.error(
                f"Push failed for subscription {subscription.id}: {e}"
            )
        return False


def is_already_notified(paciente_id: int, notification_type: str, year: int) -> bool:
    """Check if this notification was already sent."""
    return (
        NotificationLog.query.filter_by(
            paciente_id=paciente_id,
            notification_type=notification_type,
            year=year,
        ).first()
        is not None
    )


def send_birthday_notifications(dry_run: bool = False) -> dict:
    """Main orchestrator. Query birthdays for all intervals, send push notifications.

    Returns dict with counts: {'sent': N, 'skipped': N, 'failed': N}
    """
    today = date.today()
    year = today.year
    subscriptions = PushSubscription.query.all()

    results = {"sent": 0, "skipped": 0, "failed": 0}

    if not subscriptions:
        current_app.logger.info("No push subscriptions found, skipping")
        return results

    for days_ahead, interval_key in INTERVALS.items():
        patients = get_upcoming_birthdays(days_ahead)

        for paciente in patients:
            if is_already_notified(paciente.id, interval_key, year):
                results["skipped"] += 1
                continue

            if dry_run:
                nombre = f"{paciente.nombre} {paciente.apellido}"
                current_app.logger.info(
                    f"[DRY RUN] Would notify: {interval_key} for {nombre}"
                )
                results["sent"] += 1
                continue

            payload = build_notification_payload(paciente, interval_key)

            # Log BEFORE sending to prevent duplicates on partial failure
            log = NotificationLog(
                paciente_id=paciente.id,
                notification_type=interval_key,
                year=year,
            )
            db.session.add(log)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                results["skipped"] += 1
                continue

            for sub in subscriptions:
                if send_push(sub, payload):
                    results["sent"] += 1
                else:
                    results["failed"] += 1

    return results
