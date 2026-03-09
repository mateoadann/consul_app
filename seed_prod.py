"""Seed de producción: crea únicamente el usuario admin inicial."""

from sqlalchemy import text

from app import create_app
from app.extensions import db
from app.models import User


def run_seed():
    app = create_app()
    with app.app_context():
        if User.query.filter_by(username="admin").first():
            print("El usuario admin ya existe, nada que hacer.")
            return

        admin = User(username="admin", role="admin", nombre="Administrador", activo=True)
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

        # Índices trigram para búsqueda de pacientes y profesionales
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

        print("Seed de produccion completado.")
        print("Admin: admin / admin123")
        print("IMPORTANTE: cambia la contraseña del admin desde el panel.")


if __name__ == "__main__":
    run_seed()
