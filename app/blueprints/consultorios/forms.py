from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


CONSULTORIO_COLOR_CHOICES = [
    ("#EA8711", "Naranja"),
    ("#0D9488", "Turquesa"),
    ("#2563EB", "Azul"),
    ("#16A34A", "Verde"),
    ("#DC2626", "Rojo"),
    ("#7C3AED", "Violeta"),
    ("#C2410C", "Terracota"),
    ("#0891B2", "Cian"),
    ("#BE123C", "Frambuesa"),
    ("#4F46E5", "Indigo"),
]


class ConsultorioForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=50)])
    color = SelectField("Color", validators=[DataRequired()], choices=CONSULTORIO_COLOR_CHOICES)
    activo = BooleanField("Activo", default=True)
    submit = SubmitField("Guardar")
