#!/usr/bin/env python3
"""Genera variables de entorno optimizadas para deploy en seenode.com.

Uso:
    python generate_env.py                          # sin Redis
    python generate_env.py --redis redis://host:6379/0  # con Redis
    python generate_env.py --db-url postgresql+psycopg2://user:pass@host:5432/dbname
"""

import argparse
import secrets


def generate_env(db_url: str, redis_url: str | None = None) -> str:
    secret_key = secrets.token_hex(32)

    env_vars = {
        "FLASK_ENV": "production",
        "SECRET_KEY": secret_key,
        "DATABASE_URL": db_url,
        "SESSION_COOKIE_SECURE": "true",
        "UPLOADS_DIR": "./uploads",
    }

    if redis_url:
        env_vars["SESSION_TYPE"] = "redis"
        env_vars["SESSION_REDIS_URL"] = redis_url
    else:
        env_vars["SESSION_TYPE"] = "filesystem"

    return "\n".join(f"{k}={v}" for k, v in env_vars.items())


def main():
    parser = argparse.ArgumentParser(description="Genera env vars para seenode.com")
    parser.add_argument(
        "--db-url",
        default="postgresql+psycopg2://consul:consul@localhost:5432/consul_app",
        help="DATABASE_URL completa",
    )
    parser.add_argument(
        "--redis",
        default=None,
        help="URL de Redis (omitir para usar filesystem sessions)",
    )
    args = parser.parse_args()

    output = generate_env(args.db_url, args.redis)
    print(output)


if __name__ == "__main__":
    main()
