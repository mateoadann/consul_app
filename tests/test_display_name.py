from app.utils.formatting import format_display_name


class FakeEntity:
    def __init__(self, nombre, apellido, apodo=None):
        self.nombre = nombre
        self.apellido = apellido
        self.apodo = apodo


def test_format_nombre():
    e = FakeEntity("Pedro", "Gomez", "Pedrito")
    assert format_display_name(e, "nombre") == "Pedro"


def test_format_nombre_apellido():
    e = FakeEntity("Pedro", "Gomez")
    assert format_display_name(e, "nombre_apellido") == "Pedro Gomez"


def test_format_nombre_inicial():
    e = FakeEntity("Pedro", "Gomez")
    assert format_display_name(e, "nombre_inicial") == "Pedro G."


def test_format_apodo_with_apodo():
    e = FakeEntity("Pedro", "Gomez", "Pedrito")
    assert format_display_name(e, "apodo") == "Pedrito"


def test_format_apodo_fallback():
    e = FakeEntity("Pedro", "Gomez")
    assert format_display_name(e, "apodo") == "Pedro G."


def test_format_apodo_inicial_with_apodo():
    e = FakeEntity("Pedro", "Gomez", "Pedrito")
    assert format_display_name(e, "apodo_inicial") == "Pedrito G."


def test_format_apodo_inicial_fallback():
    e = FakeEntity("Pedro", "Gomez")
    assert format_display_name(e, "apodo_inicial") == "Pedro G."


def test_format_unknown_key_uses_fallback():
    e = FakeEntity("Pedro", "Gomez")
    assert format_display_name(e, "invalid") == "Pedro G."
