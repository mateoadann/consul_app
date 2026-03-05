import pytest

from app.models import User


pytestmark = pytest.mark.postgres


class TestRoleRequired:
    """Tests para el decorador @role_required."""

    def test_admin_accede_a_admin_panel(self, client, admin_user):
        """Admin puede acceder al panel de administracion."""
        client.post("/auth/login", data={"username": "admin_test", "password": "admin123"})

        response = client.get("/admin")
        assert response.status_code == 200

    def test_profesional_no_accede_a_admin_panel(self, client, profesional_user):
        """Profesional NO puede acceder al panel de administracion."""
        client.post("/auth/login", data={"username": "prof_test", "password": "prof123"})

        response = client.get("/admin")
        assert response.status_code == 403

    def test_usuario_inactivo_no_puede_login(self, client, db_session):
        """Usuario inactivo no puede hacer login."""
        user = User(username="inactivo", nombre="Usuario Inactivo", role="profesional", activo=False)
        user.set_password("secret123")
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/auth/login",
            data={"username": "inactivo", "password": "secret123"},
            follow_redirects=False,
        )
        # Login debe fallar para usuario inactivo
        assert response.status_code == 401
        assert b"Credenciales invalidas" in response.data


class TestCSRF:
    """Tests para proteccion CSRF."""

    def test_post_sin_csrf_falla(self, app, db_session):
        """POST sin token CSRF debe fallar cuando CSRF esta habilitado."""
        # Crear usuario para el test
        user = User(username="csrf_test", nombre="CSRF Test", role="admin", activo=True)
        user.set_password("csrf123")
        db_session.add(user)
        db_session.commit()

        # Habilitar CSRF temporalmente para este test
        app.config["WTF_CSRF_ENABLED"] = True

        with app.test_client() as csrf_client:
            # Login primero
            csrf_client.post("/auth/login", data={"username": "csrf_test", "password": "csrf123"})

            # Intentar POST sin CSRF token - debe fallar con 400
            response = csrf_client.post(
                "/consultorios/nuevo",
                data={
                    "nombre": "Test CSRF",
                    "color": "#EA8711",
                    "activo": "y",
                },
                follow_redirects=False,
            )
            # Flask-WTF devuelve 400 cuando CSRF falla
            assert response.status_code == 400

        # Restaurar configuracion
        app.config["WTF_CSRF_ENABLED"] = False
