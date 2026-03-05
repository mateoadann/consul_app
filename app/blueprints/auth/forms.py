from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField("Usuario", validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField("Contrasena", validators=[DataRequired()])
    submit = SubmitField("Ingresar")


class CambiarPasswordForm(FlaskForm):
    current = PasswordField("Contrasena actual", validators=[DataRequired()])
    new_password = PasswordField(
        "Nueva contrasena", validators=[DataRequired(), Length(min=6, max=128)]
    )
    submit = SubmitField("Cambiar contrasena")
