from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import AppConfig, Profesional, TurnoAudit, TurnoSerieLog, User
from app.utils.decorators import role_required
from app.utils.formatting import FORMATO_NOMBRE_OPTIONS, FORMATO_NOMBRE_DEFAULT

from .forms import ResetPasswordForm, UsuarioEditForm, UsuarioForm


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("", methods=["GET"])
@login_required
@role_required("admin")
def index():
    return render_template("admin/index.html")


@admin_bp.route("/usuarios", methods=["GET"])
@login_required
@role_required("admin")
def usuarios():
    users = User.query.order_by(User.username).all()
    return render_template("admin/usuarios.html", users=users)


@admin_bp.route("/usuarios/nuevo", methods=["GET", "POST"])
@login_required
@role_required("admin")
def nuevo_usuario():
    form = UsuarioForm()

    if form.validate_on_submit():
        existing = User.query.filter_by(username=form.username.data.strip()).first()
        if existing:
            form.username.errors.append("Ya existe un usuario con ese username.")
            return render_template("admin/usuario_form.html", form=form, is_edit=False), 422

        user = User(
            username=form.username.data.strip(),
            nombre=form.nombre.data.strip(),
            role=form.role.data,
            activo=form.activo.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        if form.role.data == "profesional":
            profesional = Profesional(
                nombre=form.nombre.data.strip(),
                apellido=form.apellido.data.strip(),
                apodo=form.apodo.data.strip() if form.apodo.data else None,
                user_id=user.id,
            )
            db.session.add(profesional)

        db.session.commit()
        flash("Usuario creado exitosamente.", "success")
        return redirect(url_for("admin.usuarios"))

    return render_template("admin/usuario_form.html", form=form, is_edit=False)


@admin_bp.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
@login_required
@role_required("admin")
def editar_usuario(user_id):
    user = User.query.get_or_404(user_id)
    form = UsuarioEditForm(obj=user)

    if request.method == "GET" and user.profesional:
        form.nombre.data = user.profesional.nombre
        form.apellido.data = user.profesional.apellido
        form.apodo.data = user.profesional.apodo

    if request.method == "GET" and not user.profesional:
        form.apellido.data = ""

    if form.validate_on_submit():
        existing = (
            User.query.filter(
                User.username == form.username.data.strip(),
                User.id != user.id,
            )
            .first()
        )
        if existing:
            form.username.errors.append("Ya existe un usuario con ese username.")
            return render_template(
                "admin/usuario_form.html", form=form, is_edit=True, user=user
            ), 422

        user.username = form.username.data.strip()
        user.nombre = form.nombre.data.strip()
        user.role = form.role.data
        user.activo = form.activo.data

        if user.profesional:
            user.profesional.nombre = form.nombre.data.strip()
            user.profesional.apellido = form.apellido.data.strip()
            user.profesional.apodo = form.apodo.data.strip() if form.apodo.data else None

        db.session.commit()
        flash("Usuario actualizado.", "success")
        return redirect(url_for("admin.usuarios"))

    return render_template("admin/usuario_form.html", form=form, is_edit=True, user=user)


@admin_bp.route("/usuarios/<int:user_id>/reset-password", methods=["GET", "POST"])
@login_required
@role_required("admin")
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    form = ResetPasswordForm()

    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(f"Contrasena de {user.username} reseteada.", "success")
        return redirect(url_for("admin.usuarios"))

    return render_template("admin/reset_password.html", form=form, user=user)


@admin_bp.route("/auditoria", methods=["GET"])
@login_required
@role_required("admin")
def auditoria():
    page = request.args.get("page", default=1, type=int)
    logs = TurnoAudit.query.order_by(TurnoAudit.created_at.desc()).paginate(
        page=page,
        per_page=40,
        error_out=False,
    )
    return render_template("admin/auditoria.html", logs=logs)


@admin_bp.route("/series", methods=["GET"])
@login_required
@role_required("admin")
def series_logs():
    page = request.args.get("page", default=1, type=int)
    logs = TurnoSerieLog.query.order_by(TurnoSerieLog.created_at.desc()).paginate(
        page=page,
        per_page=40,
        error_out=False,
    )
    return render_template("admin/series.html", logs=logs)


@admin_bp.route("/formato-nombres", methods=["GET", "POST"])
@login_required
@role_required("admin")
def formato_nombres():
    if request.method == "POST":
        fmt_paciente = request.form.get("formato_paciente", FORMATO_NOMBRE_DEFAULT)
        fmt_profesional = request.form.get("formato_profesional", FORMATO_NOMBRE_DEFAULT)

        if fmt_paciente in FORMATO_NOMBRE_OPTIONS:
            AppConfig.set("formato_nombre_paciente", fmt_paciente)
        if fmt_profesional in FORMATO_NOMBRE_OPTIONS:
            AppConfig.set("formato_nombre_profesional", fmt_profesional)

        db.session.commit()
        flash("Formato de nombres actualizado.", "success")
        return redirect(url_for("admin.formato_nombres"))

    current_paciente = AppConfig.get("formato_nombre_paciente", FORMATO_NOMBRE_DEFAULT)
    current_profesional = AppConfig.get("formato_nombre_profesional", FORMATO_NOMBRE_DEFAULT)

    return render_template(
        "admin/formato_nombres.html",
        options=FORMATO_NOMBRE_OPTIONS,
        current_paciente=current_paciente,
        current_profesional=current_profesional,
    )
