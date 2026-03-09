from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import BooleanField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class PacienteForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    apellido = StringField("Apellido", validators=[DataRequired(), Length(max=100)])
    dni = StringField("DNI", validators=[DataRequired(), Length(max=15)])
    telefono = StringField("Telefono", validators=[Optional(), Length(max=50)])
    apodo = StringField("Apodo", validators=[Optional(), Length(max=100)])
    numero_afiliado = IntegerField("Numero de afiliado", validators=[Optional(), NumberRange(min=0)])
    obra_social_id = SelectField("Obra social", coerce=int, validators=[Optional()])
    notas = TextAreaField("Notas", validators=[Optional()])
    activo = BooleanField("Activo", default=True)
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import ObraSocial
        choices = [(0, "— Sin obra social —")] + [
            (os.id, os.nombre) for os in ObraSocial.query.order_by(ObraSocial.nombre).all()
        ]
        self.obra_social_id.choices = choices


class ImportarCSVForm(FlaskForm):
    archivo = FileField("Archivo CSV", validators=[FileRequired(), FileAllowed(["csv"], "Solo archivos CSV")])
    submit = SubmitField("Importar")
