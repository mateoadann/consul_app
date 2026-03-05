from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class PacienteForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    apellido = StringField("Apellido", validators=[DataRequired(), Length(max=100)])
    dni = StringField("DNI", validators=[DataRequired(), Length(max=15)])
    telefono = StringField("Telefono", validators=[Optional(), Length(max=50)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    obra_social = StringField("Obra social", validators=[Optional(), Length(max=100)])
    notas = TextAreaField("Notas", validators=[Optional()])
    activo = BooleanField("Activo", default=True)
    submit = SubmitField("Guardar")
