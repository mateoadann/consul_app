from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class UsuarioForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(3, 50)])
    nombre = StringField("Nombre", validators=[DataRequired(), Length(1, 100)])
    apellido = StringField("Apellido", validators=[DataRequired(), Length(1, 100)])
    role = SelectField(
        "Rol",
        choices=[("profesional", "Profesional"), ("admin", "Admin")],
        validators=[DataRequired()],
    )
    activo = BooleanField("Activo", default=True)
    password = PasswordField("Contrasena", validators=[DataRequired(), Length(6, 128)])
    submit = SubmitField("Guardar")


class UsuarioEditForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(3, 50)])
    nombre = StringField("Nombre", validators=[DataRequired(), Length(1, 100)])
    apellido = StringField("Apellido", validators=[DataRequired(), Length(1, 100)])
    role = SelectField(
        "Rol",
        choices=[("profesional", "Profesional"), ("admin", "Admin")],
        validators=[DataRequired()],
    )
    activo = BooleanField("Activo")
    submit = SubmitField("Guardar")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "Nueva contrasena", validators=[DataRequired(), Length(6, 128)]
    )
    submit = SubmitField("Resetear contrasena")
