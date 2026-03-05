import pytest

from app.extensions import db
from app.models import Consultorio


pytestmark = pytest.mark.postgres


class TestConsultoriosAccess:
    """Tests de acceso al blueprint de consultorios."""

    def test_requiere_login(self, client):
        """El listado de consultorios requiere autenticacion."""
        response = client.get("/consultorios")
        assert response.status_code in (302, 401)
        if response.status_code == 302:
            assert "/auth/login" in response.headers.get("Location", "")

    def test_profesional_no_tiene_acceso(self, client, profesional_user):
        """Profesional NO puede acceder al listado de consultorios."""
        client.post("/auth/login", data={"username": "prof_test", "password": "prof123"})

        response = client.get("/consultorios")
        assert response.status_code == 403

    def test_admin_tiene_acceso(self, client, admin_user):
        """Admin puede acceder al listado de consultorios."""
        client.post("/auth/login", data={"username": "admin_test", "password": "admin123"})

        response = client.get("/consultorios")
        assert response.status_code == 200


class TestConsultoriosCRUD:
    """Tests CRUD de consultorios."""

    def test_crear_consultorio(self, client, admin_user):
        """Admin puede crear un consultorio."""
        client.post("/auth/login", data={"username": "admin_test", "password": "admin123"})

        response = client.post(
            "/consultorios/nuevo",
            data={
                "nombre": "Consultorio Nuevo",
                "color": "#EA8711",  # Naranja - valor valido del SelectField
                "activo": "y",
            },
            follow_redirects=False,
        )
        assert response.status_code in (302, 303)

        consultorio = Consultorio.query.filter_by(nombre="Consultorio Nuevo").first()
        assert consultorio is not None
        assert consultorio.color == "#EA8711"
        assert consultorio.activo is True

    def test_crear_consultorio_nombre_duplicado(self, client, admin_user, consultorio):
        """No se puede crear consultorio con nombre duplicado."""
        client.post("/auth/login", data={"username": "admin_test", "password": "admin123"})

        response = client.post(
            "/consultorios/nuevo",
            data={
                "nombre": "Consultorio Test",  # Mismo nombre que el fixture
                "color": "#EA8711",  # Naranja - valor valido del SelectField
                "activo": "y",
            },
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert b"Ya existe un consultorio con ese nombre" in response.data
