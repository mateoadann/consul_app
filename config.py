import os
from datetime import timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://consul:consul@localhost:5432/consul_app"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_TYPE = os.getenv("SESSION_TYPE", "filesystem")
    SESSION_REDIS_URL = os.getenv("SESSION_REDIS_URL", "redis://localhost:6379/0")
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

    WTF_CSRF_TIME_LIMIT = None

    APP_TITLE = "ConsulApp"
    UPLOADS_DIR = os.getenv("UPLOADS_DIR", str(BASE_DIR / "uploads"))

    # VAPID keys for Web Push notifications
    VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
    VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
    VAPID_SUBJECT = os.environ.get("VAPID_SUBJECT", "mailto:admin@consulapp.com")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SESSION_TYPE = "filesystem"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        os.getenv("DATABASE_URL", "postgresql+psycopg2://consul:consul@localhost:5432/consul_app_test")
    )


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
