import pytest

from app.extensions import db
from app.models import Paciente, User


pytestmark = pytest.mark.postgres


def test_crear_paciente(client):
    user = User(username="pro1", role="profesional", nombre="Pro Uno", activo=True)
    user.set_password("secret")
    db.session.add(user)
    db.session.commit()

    client.post("/auth/login", data={"username": "pro1", "password": "secret"})

    response = client.post(
        "/pacientes/nuevo",
        data={
            "nombre": "Pedro",
            "apellido": "Perez",
            "dni": "30000001",
            "telefono": "111",
            "apodo": "",
            "numero_afiliado": "",
            "obra_social_id": "0",
            "notas": "",
            "activo": "y",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert Paciente.query.filter_by(dni="30000001").first() is not None
