import os

import redis
from dotenv import load_dotenv
from flask import Flask, request
from flask_login import current_user

from config import config_by_name

from .extensions import csrf, db, login_manager, migrate, session_ext
from .utils.formatting import (
    format_display_name,
    format_fecha_agenda,
    format_fecha_agenda_corta,
    format_fecha_corta,
    format_fecha_hora_corta,
    format_hora_24,
)


def create_app(config_name: str | None = None) -> Flask:
    load_dotenv()

    app = Flask(__name__)

    env_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(env_name, config_by_name["development"]))

    if app.config.get("SESSION_TYPE") == "redis":
        app.config["SESSION_REDIS"] = redis.from_url(app.config["SESSION_REDIS_URL"])

    uploads_dir = app.config.get("UPLOADS_DIR")
    if uploads_dir:
        os.makedirs(uploads_dir, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    session_ext.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Ingresa para continuar."

    from .models import User  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    register_blueprints(app)
    register_template_filters(app)
    register_request_hooks(app)
    register_security_headers(app)
    register_error_handlers(app)
    register_cli_commands(app)

    return app


def register_blueprints(app: Flask) -> None:
    from .blueprints.admin.routes import admin_bp
    from .blueprints.agenda.routes import agenda_bp
    from .blueprints.auth.routes import auth_bp
    from .blueprints.consultorios.routes import consultorios_bp
    from .blueprints.obra_sociales.routes import obra_sociales_bp
    from .blueprints.pacientes.routes import pacientes_bp
    from .blueprints.profesionales.routes import profesionales_bp
    from .blueprints.turnos.routes import turnos_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(agenda_bp)
    app.register_blueprint(turnos_bp)
    app.register_blueprint(pacientes_bp)
    app.register_blueprint(profesionales_bp)
    app.register_blueprint(consultorios_bp)
    app.register_blueprint(obra_sociales_bp)
    app.register_blueprint(admin_bp)


def register_request_hooks(app: Flask) -> None:
    @app.before_request
    def attach_audit_metadata():
        if current_user.is_authenticated:
            db.session.info["audit_user_id"] = current_user.id
        else:
            db.session.info["audit_user_id"] = None

        forwarded_for = request.headers.get("X-Forwarded-For", "")
        ip = forwarded_for.split(",")[0].strip() if forwarded_for else request.remote_addr
        db.session.info["audit_ip"] = ip

    @app.before_request
    def load_display_name_config():
        from flask import g
        from .models.app_config import AppConfig
        from .utils.formatting import FORMATO_NOMBRE_DEFAULT
        g.fmt_paciente = AppConfig.get("formato_nombre_paciente", FORMATO_NOMBRE_DEFAULT)
        g.fmt_profesional = AppConfig.get("formato_nombre_profesional", FORMATO_NOMBRE_DEFAULT)

    @app.teardown_request
    def clear_session_info(_exc):
        db.session.info.pop("audit_user_id", None)
        db.session.info.pop("audit_ip", None)


def register_template_filters(app: Flask) -> None:
    app.jinja_env.filters["fecha_agenda"] = format_fecha_agenda
    app.jinja_env.filters["fecha_agenda_corta"] = format_fecha_agenda_corta
    app.jinja_env.filters["fecha_corta"] = format_fecha_corta
    app.jinja_env.filters["fecha_hora_corta"] = format_fecha_hora_corta
    app.jinja_env.filters["hora_24"] = format_hora_24

    def _display_name_paciente(paciente):
        from flask import g
        fmt = getattr(g, "fmt_paciente", "nombre_inicial")
        return format_display_name(paciente, fmt)

    def _display_name_profesional(profesional):
        from flask import g
        fmt = getattr(g, "fmt_profesional", "nombre_inicial")
        return format_display_name(profesional, fmt)

    app.jinja_env.filters["display_name_paciente"] = _display_name_paciente
    app.jinja_env.filters["display_name_profesional"] = _display_name_profesional


def register_security_headers(app: Flask) -> None:
    @app.after_request
    def set_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers[
            "Content-Security-Policy"
        ] = (
            "default-src 'self'; "
            "script-src 'self' https://unpkg.com; "
            "connect-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;"
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data:;"
        )
        return response


def register_cli_commands(app: Flask) -> None:
    import click

    @app.cli.command("ensure-admin")
    @click.option("--username", default="admin")
    @click.option("--password", default="admin123")
    def ensure_admin(username: str, password: str) -> None:
        """Create default admin user if no admin exists."""
        from .models import User

        if User.query.filter_by(role="admin").first():
            click.echo("[ok] Admin user already exists, skipping.")
            return

        user = User(username=username, role="admin", nombre="Administrador", activo=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"[ok] Admin user '{username}' created.")


def register_error_handlers(app: Flask) -> None:
    from flask import render_template

    @app.errorhandler(403)
    def forbidden(_err):
        return (
            render_template(
                "errors/error.html",
                code=403,
                message="No autorizado. Esta seccion requiere usuario admin.",
            ),
            403,
        )

    @app.errorhandler(404)
    def not_found(_err):
        return render_template("errors/error.html", code=404, message="No encontrado."), 404

    @app.errorhandler(500)
    def server_error(_err):
        return (
            render_template(
                "errors/error.html",
                code=500,
                message="Ocurrio un error. Intenta de nuevo.",
            ),
            500,
        )
