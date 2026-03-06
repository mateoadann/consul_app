from datetime import date, datetime, time, timedelta

from psycopg2.extras import DateTimeRange
from sqlalchemy import text

from app import create_app
from app.extensions import db
from app.models import Consultorio, Paciente, Profesional, Turno, User


def get_or_create_user(username, password, role, nombre):
    user = User.query.filter_by(username=username).first()
    if user:
        return user
    user = User(username=username, role=role, nombre=nombre, activo=True)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user


def get_or_create_profesional(nombre, apellido, especialidad, username):
    user = User.query.filter_by(username=username).first()
    if not user:
        raise ValueError(f"User '{username}' must exist before creating Profesional")

    profesional = Profesional.query.filter_by(user_id=user.id).first()
    if profesional:
        return profesional

    profesional = Profesional(
        nombre=nombre,
        apellido=apellido,
        especialidad=especialidad,
        telefono="",
        email=f"{username}@consulapp.local",
        activo=True,
        user_id=user.id,
    )
    db.session.add(profesional)
    db.session.flush()
    return profesional


def get_or_create_consultorio(nombre, color):
    item = Consultorio.query.filter_by(nombre=nombre).first()
    if item:
        if item.color != color:
            item.color = color
        return item
    item = Consultorio(nombre=nombre, color=color, activo=True)
    db.session.add(item)
    db.session.flush()
    return item


def get_or_create_paciente(nombre, apellido, dni, telefono):
    paciente = Paciente.query.filter_by(dni=dni).first()
    if paciente:
        return paciente
    paciente = Paciente(
        nombre=nombre,
        apellido=apellido,
        dni=dni,
        telefono=telefono,
        email=None,
        obra_social="Particular",
        notas=None,
        activo=True,
    )
    db.session.add(paciente)
    db.session.flush()
    return paciente


def build_seed_turno(fecha, hh, mm, dur_min, paciente, profesional, consultorio, creator):
    start = datetime.combine(fecha, time(hour=hh, minute=mm))
    end = start + timedelta(minutes=dur_min)
    return Turno(
        paciente_id=paciente.id,
        profesional_id=profesional.id,
        consultorio_id=consultorio.id,
        durante=DateTimeRange(start, end, "[)"),
        estado="reservado",
        created_by=creator.id,
    )


def run_seed():
    app = create_app()
    with app.app_context():
        try:
            db.session.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
            db.session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            db.session.commit()
        except Exception:
            db.session.rollback()

        db.create_all()

        admin = get_or_create_user("admin", "admin123", "admin", "Administrador")
        dr_garcia_user = get_or_create_user("garcia", "garcia123", "profesional", "Dr. Garcia")
        dr_ruiz_user = get_or_create_user("ruiz", "ruiz123", "profesional", "Dr. Ruiz")
        lic_perez_user = get_or_create_user("perez", "perez123", "profesional", "Lic. Perez")

        prof_1 = get_or_create_profesional("Carla", "Garcia", "Clinica", "garcia")
        prof_2 = get_or_create_profesional("Santiago", "Ruiz", "Cardiologia", "ruiz")
        prof_3 = get_or_create_profesional("Alicia", "Perez", "Kinesiologia", "perez")

        c1 = get_or_create_consultorio("Consultorio 1", "#EA8711")
        c2 = get_or_create_consultorio("Consultorio 2", "#0D9488")
        c3 = get_or_create_consultorio("Consultorio 3", "#2563EB")

        for profesional in (prof_1, prof_2, prof_3):
            profesional.consultorios = [c1, c2, c3]

        p1 = get_or_create_paciente("Maria", "Gonzalez", "30456789", "11-5555-1234")
        p2 = get_or_create_paciente("Pedro", "Gomez", "28123456", "11-5252-8888")
        p3 = get_or_create_paciente("Lucia", "Lopez", "29555111", "11-4333-2211")
        p4 = get_or_create_paciente("Nicolas", "Martinez", "31222000", "11-4444-9999")
        p5 = get_or_create_paciente("Ana", "Diaz", "33222111", "11-1111-7777")

        db.session.commit()

        db.session.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_pacientes_nombre_apellido_trgm "
                "ON pacientes USING gin ((nombre || ' ' || apellido) gin_trgm_ops)"
            )
        )
        db.session.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_profesionales_nombre_apellido_trgm "
                "ON profesionales USING gin ((nombre || ' ' || apellido) gin_trgm_ops)"
            )
        )
        db.session.commit()

        today = date.today()
        if Turno.query.count() == 0:
            db.session.add(
                build_seed_turno(today, 8, 0, 30, p1, prof_1, c1, dr_ruiz_user)
            )
            db.session.add(
                build_seed_turno(today, 9, 0, 30, p2, prof_2, c2, dr_ruiz_user)
            )
            db.session.add(
                build_seed_turno(today, 9, 30, 30, p3, prof_3, c3, dr_garcia_user)
            )
            db.session.add(
                build_seed_turno(today, 10, 0, 45, p4, prof_1, c1, admin)
            )
            db.session.add(
                build_seed_turno(today, 11, 15, 30, p5, prof_2, c2, lic_perez_user)
            )

        db.session.commit()
        print("Seed completado.")
        print("Admin: admin / admin123")


if __name__ == "__main__":
    run_seed()
