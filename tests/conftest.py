import os
import pathlib
import sys

# Add project root to path before importing app modules
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


def pytest_configure(config):
    config.addinivalue_line("markers", "postgres: requiere Postgres real")


def pytest_collection_modifyitems(config, items):
    if TEST_DATABASE_URL:
        return
    skip_marker = pytest.mark.skip(reason="Defini TEST_DATABASE_URL para correr tests de integracion")
    for item in items:
        if "postgres" in item.keywords:
            item.add_marker(skip_marker)


@pytest.fixture
def app():
    app = create_app("testing")

    with app.app_context():
        if TEST_DATABASE_URL:
            db.drop_all()
            db.create_all()
        yield app
        if TEST_DATABASE_URL:
            db.session.remove()
            db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Proporciona acceso a db.session dentro del contexto de app."""
    yield db.session


@pytest.fixture
def admin_user(app, db_session):
    """Usuario con rol admin."""
    from app.models import User
    user = User(username="admin_test", nombre="Admin Test", role="admin")
    user.set_password("admin123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def profesional_user(app, db_session):
    """Usuario con rol profesional."""
    from app.models import User, Profesional
    user = User(username="prof_test", nombre="Prof Test", role="profesional")
    user.set_password("prof123")
    db_session.add(user)
    db_session.commit()

    profesional = Profesional(
        nombre="Test",
        apellido="Profesional",
        especialidad="General",
        user_id=user.id
    )
    db_session.add(profesional)
    db_session.commit()
    return user


@pytest.fixture
def consultorio(app, db_session):
    """Consultorio de prueba."""
    from app.models import Consultorio
    c = Consultorio(nombre="Consultorio Test", color="naranja", activo=True)
    db_session.add(c)
    db_session.commit()
    return c
