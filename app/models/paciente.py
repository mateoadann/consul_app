from app.extensions import db
from app.models.base import TimestampMixin


class Paciente(TimestampMixin, db.Model):
    __tablename__ = "pacientes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(15), nullable=False, unique=True)
    telefono = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    obra_social = db.Column(db.String(100), nullable=True)
    notas = db.Column(db.Text, nullable=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    turnos = db.relationship("Turno", back_populates="paciente", lazy="dynamic")

    @property
    def nombre_completo(self) -> str:
        return f"{self.apellido}, {self.nombre}"

    def __repr__(self) -> str:
        return f"<Paciente {self.apellido}, {self.nombre}>"
