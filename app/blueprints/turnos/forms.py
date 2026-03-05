from datetime import date, datetime, time

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import ValidationError
from wtforms.validators import DataRequired, NumberRange, Optional

from app.utils.helpers import build_time_choices, is_15_minute_increment, is_time_in_agenda_range, parse_hhmm


HORA_INICIO_CHOICES = build_time_choices(time(hour=8, minute=0), time(hour=19, minute=45))
HORA_FIN_CHOICES = build_time_choices(time(hour=8, minute=15), time(hour=20, minute=0))


class TurnoForm(FlaskForm):
    fecha = DateField("Fecha", validators=[DataRequired()], format="%Y-%m-%d")
    hora_inicio = SelectField(
        "Hora inicio",
        validators=[DataRequired()],
        choices=HORA_INICIO_CHOICES,
    )
    hora_fin = SelectField(
        "Hora fin",
        validators=[DataRequired()],
        choices=HORA_FIN_CHOICES,
    )
    consultorio_id = SelectField("Consultorio", coerce=int, validators=[DataRequired()])
    profesional_id = SelectField("Profesional", coerce=int, validators=[DataRequired()])
    paciente_query = StringField("Paciente", validators=[DataRequired()])
    paciente_id = HiddenField("Paciente ID", validators=[DataRequired()])
    repetir = BooleanField("Repetir")
    cada_n_semanas = IntegerField(
        "Cada N semanas",
        validators=[Optional(), NumberRange(min=1, max=12)],
        default=1,
    )
    fecha_limite = DateField("Fecha limite", validators=[Optional()], format="%Y-%m-%d")
    recurrencia_patrones = HiddenField("Patrones", validators=[Optional()])
    submit = SubmitField("Reservar turno")

    def validate_hora_inicio(self, field):
        selected = parse_hhmm(field.data)
        if not selected:
            raise ValidationError("Selecciona una hora valida.")
        if not is_15_minute_increment(selected):
            raise ValidationError("La hora debe ser en intervalos de 15 minutos.")
        if not is_time_in_agenda_range(selected):
            raise ValidationError("La hora debe estar entre 08:00 y 20:00.")

    def validate_hora_fin(self, field):
        end_time = parse_hhmm(field.data)
        start_time = parse_hhmm(self.hora_inicio.data)

        if not end_time:
            raise ValidationError("Selecciona una hora valida.")
        if not is_15_minute_increment(end_time):
            raise ValidationError("La hora debe ser en intervalos de 15 minutos.")
        if not is_time_in_agenda_range(end_time):
            raise ValidationError("La hora debe estar entre 08:00 y 20:00.")
        if start_time and end_time <= start_time:
            raise ValidationError("La hora fin debe ser mayor a la hora inicio.")
        if start_time:
            start_at = datetime.combine(date.today(), start_time)
            end_at = datetime.combine(date.today(), end_time)
            duration = int((end_at - start_at).total_seconds() / 60)
            if duration < 15 or duration > 120:
                raise ValidationError("La duracion debe estar entre 15 y 120 minutos.")


class EstadoTurnoForm(FlaskForm):
    estado = SelectField(
        "Estado",
        choices=[("confirmado", "Confirmado"), ("atendido", "Atendido"), ("cancelado", "Cancelado")],
        validators=[DataRequired()],
    )
    motivo_cancelacion = TextAreaField("Motivo cancelacion", validators=[Optional()])
    submit = SubmitField("Guardar")
