"""Crea las extensiones PostgreSQL necesarias antes de correr migraciones."""

import os
import sys

import psycopg2


def main():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL no está configurada")
        sys.exit(1)

    # psycopg2 no acepta el prefijo +psycopg2 de SQLAlchemy
    dsn = url.replace("postgresql+psycopg2://", "postgresql://")

    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

        # Limpiar DB corrupta del deploy fallido (sin alembic_version pero con tablas/enums)
        # TODO: eliminar este bloque después del primer deploy exitoso
        cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='alembic_version')")
        has_alembic = cur.fetchone()[0]
        if not has_alembic:
            print("WARN: no existe alembic_version, limpiando esquema huérfano...")
            cur.execute("DROP TABLE IF EXISTS turnos_series_log CASCADE")
            cur.execute("DROP TABLE IF EXISTS turnos_audit CASCADE")
            cur.execute("DROP TABLE IF EXISTS turnos CASCADE")
            cur.execute("DROP TABLE IF EXISTS profesional_consultorio CASCADE")
            cur.execute("DROP TABLE IF EXISTS profesionales CASCADE")
            cur.execute("DROP TABLE IF EXISTS consultorios CASCADE")
            cur.execute("DROP TABLE IF EXISTS pacientes CASCADE")
            cur.execute("DROP TABLE IF EXISTS users CASCADE")
            cur.execute("DROP TYPE IF EXISTS user_role_enum")
            cur.execute("DROP TYPE IF EXISTS turno_estado_enum")
            print("OK: esquema huérfano limpiado")

        cur.close()
        conn.close()
        print("OK: extensiones btree_gist y pg_trgm verificadas")
    except Exception as e:
        print(f"ERROR creando extensiones: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
