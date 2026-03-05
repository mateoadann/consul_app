import pytest

from app.extensions import db
from app.models import User


pytestmark = pytest.mark.postgres


def test_login_logout_cycle(client):
    user = User(username="demo", role="profesional", nombre="Demo", activo=True)
    user.set_password("secret123")
    db.session.add(user)
    db.session.commit()

    response = client.post(
        "/auth/login",
        data={"username": "demo", "password": "secret123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Agenda" in response.data

    response = client.post("/auth/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Ingresar" in response.data
