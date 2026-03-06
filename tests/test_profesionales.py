import pytest

from app.extensions import db
from app.models import Profesional, User


pytestmark = pytest.mark.postgres


class TestProfesionalesIndex:
    """Tests para el listado de profesionales."""

    def test_requiere_login(self, client):
        """El listado de profesionales requiere autenticacion."""
        response = client.get("/profesionales")
        assert response.status_code in (302, 401)
        if response.status_code == 302:
            assert "/auth/login" in response.headers.get("Location", "")

    def test_lista_profesionales_como_admin(self, client, admin_user):
        """Admin puede ver el listado de profesionales."""
        client.post("/auth/login", data={"username": "admin_test", "password": "admin123"})

        # Crear usuarios y profesionales vinculados (relacion 1:1 obligatoria)
        u1 = User(username="ana_g", nombre="Ana Garcia", role="profesional")
        u1.set_password("test123")
        u2 = User(username="carlos_l", nombre="Carlos Lopez", role="profesional")
        u2.set_password("test123")
        db.session.add_all([u1, u2])
        db.session.flush()

        p1 = Profesional(nombre="Ana", apellido="Garcia", activo=True, user_id=u1.id)
        p2 = Profesional(nombre="Carlos", apellido="Lopez", activo=True, user_id=u2.id)
        db.session.add_all([p1, p2])
        db.session.commit()

        response = client.get("/profesionales")
        assert response.status_code == 200
        assert b"Ana" in response.data or b"Garcia" in response.data

    def test_lista_profesionales_como_profesional(self, client, profesional_user):
        """Profesional NO puede ver el listado de profesionales (solo admin)."""
        client.post("/auth/login", data={"username": "prof_test", "password": "prof123"})

        response = client.get("/profesionales")
        assert response.status_code == 403


class TestProfesionalesAutocomplete:
    """Tests para el autocomplete de profesionales."""

    def test_autocomplete_requiere_login(self, client):
        """El autocomplete requiere autenticacion."""
        response = client.get("/profesionales/htmx/buscar?q=test")
        assert response.status_code in (302, 401)

    def test_autocomplete_retorna_resultados(self, client, profesional_user):
        """El autocomplete retorna resultados para usuarios autenticados."""
        client.post("/auth/login", data={"username": "prof_test", "password": "prof123"})

        # El profesional_user ya tiene un Profesional asociado con apellido "Profesional"
        response = client.get("/profesionales/htmx/buscar?q=Profesional")
        assert response.status_code == 200
        assert b"Profesional" in response.data

    def test_autocomplete_query_corta_retorna_vacio(self, client, profesional_user):
        """Query menor a 2 caracteres retorna vacio."""
        client.post("/auth/login", data={"username": "prof_test", "password": "prof123"})

        response = client.get("/profesionales/htmx/buscar?q=a")
        assert response.status_code == 200
        assert response.data == b""
