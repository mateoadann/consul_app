import json
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app.extensions import db
from app.models import NotificationLog, Paciente, PushSubscription, User


pytestmark = pytest.mark.postgres


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(session, username="notif_user", role="profesional"):
    user = User(username=username, nombre="Test User", role=role, activo=True)
    user.set_password("secret")
    session.add(user)
    session.commit()
    return user


def _login(client, username="notif_user", password="secret"):
    client.post("/auth/login", data={"username": username, "password": password})


def _make_paciente(session, nombre="Juan", apellido="Perez", dni="99000001",
                   cumpleanos=None, activo=True):
    p = Paciente(
        nombre=nombre,
        apellido=apellido,
        dni=dni,
        cumpleanos=cumpleanos,
        activo=activo,
    )
    session.add(p)
    session.commit()
    return p


# ---------------------------------------------------------------------------
# 8.1 — Birthday query tests
# ---------------------------------------------------------------------------

class TestGetUpcomingBirthdays:

    def test_birthday_today(self, app):
        """Patient with birthday today should be returned."""
        from app.services.notifications import get_upcoming_birthdays

        today = date.today()
        # Use a past year so it's clearly a birthday, not the actual creation date
        bday = today.replace(year=today.year - 30)
        _make_paciente(db.session, dni="81000001", cumpleanos=bday)

        results = get_upcoming_birthdays(0)
        assert len(results) == 1
        assert results[0].dni == "81000001"

    def test_birthday_in_5_days(self, app):
        """Patient with birthday in 5 days should be returned."""
        from app.services.notifications import get_upcoming_birthdays

        target = date.today() + timedelta(days=5)
        bday = target.replace(year=target.year - 25)
        _make_paciente(db.session, dni="81000002", cumpleanos=bday)

        results = get_upcoming_birthdays(5)
        assert len(results) == 1
        assert results[0].dni == "81000002"

    def test_no_birthday_match(self, app):
        """Patient with birthday on different date should not be returned."""
        from app.services.notifications import get_upcoming_birthdays

        # Birthday is 60 days from now — won't match 0 or 5 days ahead
        far_away = date.today() + timedelta(days=60)
        bday = far_away.replace(year=far_away.year - 20)
        _make_paciente(db.session, dni="81000003", cumpleanos=bday)

        results = get_upcoming_birthdays(0)
        assert len(results) == 0

    def test_inactive_patient_excluded(self, app):
        """Inactive patients should not appear in birthday results."""
        from app.services.notifications import get_upcoming_birthdays

        today = date.today()
        bday = today.replace(year=today.year - 30)
        _make_paciente(db.session, dni="81000004", cumpleanos=bday, activo=False)

        results = get_upcoming_birthdays(0)
        assert len(results) == 0

    def test_feb29_in_non_leap_year(self, app):
        """Feb 29 birthday should match on Feb 28 in non-leap years."""
        from app.services.notifications import get_upcoming_birthdays

        # Simulate: today is Feb 28 of a non-leap year, patient born on Feb 29
        feb29_bday = date(2000, 2, 29)  # 2000 is a leap year
        _make_paciente(db.session, dni="81000005", cumpleanos=feb29_bday)

        # Mock date.today() to return Feb 28 of a non-leap year
        fake_today = date(2025, 2, 28)  # 2025 is NOT a leap year
        with patch("app.services.notifications.date") as mock_date:
            mock_date.today.return_value = fake_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            results = get_upcoming_birthdays(0)

        dnies = [p.dni for p in results]
        assert "81000005" in dnies


# ---------------------------------------------------------------------------
# 8.2 — Subscription endpoint tests
# ---------------------------------------------------------------------------

class TestSubscriptionEndpoints:

    def test_subscribe(self, client):
        """POST /notifications/subscribe should store subscription."""
        user = _make_user(db.session)
        _login(client)

        resp = client.post(
            "/notifications/subscribe",
            data=json.dumps({
                "endpoint": "https://push.example.com/sub1",
                "keys": {"p256dh": "test-p256dh-key", "auth": "test-auth-key"},
            }),
            content_type="application/json",
        )
        assert resp.status_code == 201

        sub = PushSubscription.query.filter_by(endpoint="https://push.example.com/sub1").first()
        assert sub is not None
        assert sub.user_id == user.id
        assert sub.p256dh == "test-p256dh-key"
        assert sub.auth == "test-auth-key"

    def test_subscribe_upsert(self, client):
        """Re-subscribing with same endpoint should update, not duplicate."""
        _make_user(db.session)
        _login(client)

        payload = {
            "endpoint": "https://push.example.com/sub2",
            "keys": {"p256dh": "old-key", "auth": "old-auth"},
        }
        client.post(
            "/notifications/subscribe",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Re-subscribe with updated keys
        payload["keys"] = {"p256dh": "new-key", "auth": "new-auth"}
        resp = client.post(
            "/notifications/subscribe",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 201

        subs = PushSubscription.query.filter_by(endpoint="https://push.example.com/sub2").all()
        assert len(subs) == 1
        assert subs[0].p256dh == "new-key"
        assert subs[0].auth == "new-auth"

    def test_unsubscribe(self, client):
        """DELETE /notifications/unsubscribe should remove subscription."""
        user = _make_user(db.session)
        _login(client)

        # Create subscription directly
        sub = PushSubscription(
            user_id=user.id,
            endpoint="https://push.example.com/sub3",
            p256dh="key",
            auth="auth",
        )
        db.session.add(sub)
        db.session.commit()

        resp = client.delete(
            "/notifications/unsubscribe",
            data=json.dumps({"endpoint": "https://push.example.com/sub3"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert PushSubscription.query.filter_by(endpoint="https://push.example.com/sub3").first() is None

    def test_subscribe_requires_login(self, client):
        """Unauthenticated request should be rejected."""
        resp = client.post(
            "/notifications/subscribe",
            data=json.dumps({
                "endpoint": "https://push.example.com/anon",
                "keys": {"p256dh": "k", "auth": "a"},
            }),
            content_type="application/json",
        )
        # Flask-Login redirects to login page (302) or returns 401
        assert resp.status_code in (302, 401)

    def test_subscribe_missing_keys(self, client):
        """Request without keys should return 400."""
        _make_user(db.session)
        _login(client)

        resp = client.post(
            "/notifications/subscribe",
            data=json.dumps({"endpoint": "https://push.example.com/bad"}),
            content_type="application/json",
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# 8.3 — Idempotency tests
# ---------------------------------------------------------------------------

class TestNotificationIdempotency:

    def test_notification_not_sent_twice(self, app):
        """NotificationLog prevents duplicate sends."""
        from app.services.notifications import is_already_notified

        paciente = _make_paciente(db.session, dni="83000001")

        log = NotificationLog(
            paciente_id=paciente.id,
            notification_type="today",
            year=2026,
        )
        db.session.add(log)
        db.session.commit()

        assert is_already_notified(paciente.id, "today", 2026) is True

    def test_not_notified_different_year(self, app):
        """Same patient, same type, different year should not be flagged."""
        from app.services.notifications import is_already_notified

        paciente = _make_paciente(db.session, dni="83000002")

        log = NotificationLog(
            paciente_id=paciente.id,
            notification_type="today",
            year=2025,
        )
        db.session.add(log)
        db.session.commit()

        assert is_already_notified(paciente.id, "today", 2026) is False

    def test_not_notified_different_type(self, app):
        """Same patient, same year, different type should not be flagged."""
        from app.services.notifications import is_already_notified

        paciente = _make_paciente(db.session, dni="83000003")

        log = NotificationLog(
            paciente_id=paciente.id,
            notification_type="5_days",
            year=2026,
        )
        db.session.add(log)
        db.session.commit()

        assert is_already_notified(paciente.id, "today", 2026) is False


# ---------------------------------------------------------------------------
# 8.4 — Cleanup / stale subscription test
# ---------------------------------------------------------------------------

class TestStaleSubscriptionCleanup:

    def test_stale_subscription_deleted(self, app):
        """Deleting a PushSubscription removes it from the database."""
        user = _make_user(db.session, username="cleanup_user")

        sub = PushSubscription(
            user_id=user.id,
            endpoint="https://push.example.com/stale",
            p256dh="key",
            auth="auth",
        )
        db.session.add(sub)
        db.session.commit()
        sub_id = sub.id

        db.session.delete(sub)
        db.session.commit()

        assert PushSubscription.query.get(sub_id) is None

    def test_send_push_deletes_on_410(self, app):
        """send_push should delete subscription when push service returns 410."""
        from unittest.mock import MagicMock

        from app.services.notifications import send_push

        user = _make_user(db.session, username="push410_user")
        sub = PushSubscription(
            user_id=user.id,
            endpoint="https://push.example.com/gone",
            p256dh="key",
            auth="auth",
        )
        db.session.add(sub)
        db.session.commit()
        sub_id = sub.id

        # Mock pywebpush to raise WebPushException with 410 response
        from pywebpush import WebPushException
        mock_response = MagicMock()
        mock_response.status_code = 410

        with patch("app.services.notifications.webpush") as mock_webpush, \
             patch.dict(app.config, {
                 "VAPID_PRIVATE_KEY": "fake-key",
                 "VAPID_SUBJECT": "mailto:test@example.com",
             }):
            mock_webpush.side_effect = WebPushException("Gone", response=mock_response)

            result = send_push(sub, {"title": "test", "body": "test"})

        assert result is False
        assert PushSubscription.query.get(sub_id) is None
