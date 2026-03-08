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
        # Limpiar alembic_version si quedó de un intento fallido
        cur.execute("DROP TABLE IF EXISTS alembic_version")
        cur.close()
        conn.close()
        print("OK: extensiones creadas, alembic_version limpiado")
    except Exception as e:
        print(f"ERROR creando extensiones: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
