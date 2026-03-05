from app.extensions import db
from app.models.base import TimestampMixin


class TurnoSerieLog(TimestampMixin, db.Model):
    __tablename__ = "turnos_series_log"

    id = db.Column(db.Integer, primary_key=True)
    serie_id = db.Column(db.String(36), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False)
    profesional_id = db.Column(db.Integer, db.ForeignKey("profesionales.id"), nullable=False)

    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_limite = db.Column(db.Date, nullable=False)
    cada_n_semanas = db.Column(db.Integer, nullable=False, default=1)

    patrones_json = db.Column(db.JSON, nullable=False)
    total_intentados = db.Column(db.Integer, nullable=False, default=0)
    total_creados = db.Column(db.Integer, nullable=False, default=0)
    total_fallidos = db.Column(db.Integer, nullable=False, default=0)
    fallidos_json = db.Column(db.JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<TurnoSerieLog {self.serie_id} {self.total_creados}/{self.total_intentados}>"
