import io

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


def test_importar_csv(client, admin_user):
    from app.models import ObraSocial
    os_obj = ObraSocial(nombre="OSDE")
    db.session.add(os_obj)
    db.session.commit()

    client.post("/auth/login", data={"username": "admin_test", "password": "admin123"})

    csv_content = f"nombre,apellido,dni,telefono,numero_afiliado,obra_social_id,notas,apodo\nJuan,Perez,40000001,1155551234,12345,{os_obj.id},nota test,Juancito\nMaria,Lopez,40000002,,,,,"
    data = {
        "archivo": (io.BytesIO(csv_content.encode("utf-8")), "pacientes.csv"),
    }
    response = client.post("/pacientes/importar", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    assert Paciente.query.filter_by(dni="40000001").first() is not None
    assert Paciente.query.filter_by(dni="40000002").first() is not None
    p1 = Paciente.query.filter_by(dni="40000001").first()
    assert p1.numero_afiliado == 12345
    assert p1.obra_social_id == os_obj.id
    assert p1.apodo == "Juancito"


def test_importar_csv_skip_duplicate(client, admin_user):
    client.post("/auth/login", data={"username": "admin_test", "password": "admin123"})

    existing = Paciente(nombre="Existing", apellido="Patient", dni="50000001", activo=True)
    db.session.add(existing)
    db.session.commit()

    csv_content = "nombre,apellido,dni,telefono,numero_afiliado,obra_social_id,notas,apodo\nExisting,Patient,50000001,,,,,"
    data = {"archivo": (io.BytesIO(csv_content.encode("utf-8")), "pacientes.csv")}
    response = client.post("/pacientes/importar", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    assert Paciente.query.filter_by(dni="50000001").count() == 1
