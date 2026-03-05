from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.models import User

from app.extensions import db

from .forms import CambiarPasswordForm, LoginForm


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("agenda.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if not user or not user.activo or not user.check_password(form.password.data):
            flash("Credenciales invalidas.", "error")
            return render_template("auth/login.html", form=form), 401

        login_user(user, remember=False)
        next_url = request.args.get("next")
        return redirect(next_url or url_for("agenda.index"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/cambiar-password", methods=["GET", "POST"])
@login_required
def cambiar_password():
    form = CambiarPasswordForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current.data):
            form.current.errors.append("Contrasena actual incorrecta.")
            return render_template("auth/cambiar_password.html", form=form), 422

        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Contrasena actualizada exitosamente.", "success")
        return redirect(url_for("agenda.index"))

    return render_template("auth/cambiar_password.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Sesion finalizada.", "success")
    return redirect(url_for("auth.login"))
