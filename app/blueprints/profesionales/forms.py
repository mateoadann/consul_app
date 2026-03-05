from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional


class ProfesionalForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    apellido = StringField("Apellido", validators=[DataRequired(), Length(max=100)])
    especialidad = StringField("Especialidad", validators=[Optional(), Length(max=100)])
    telefono = StringField("Telefono", validators=[Optional(), Length(max=50)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    activo = BooleanField("Activo", default=True)
    submit = SubmitField("Guardar")
