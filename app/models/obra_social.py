from app.extensions import db
from app.models.base import TimestampMixin


class ObraSocial(TimestampMixin, db.Model):
    __tablename__ = "obra_sociales"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)

    pacientes = db.relationship("Paciente", back_populates="obra_social")

    def __repr__(self) -> str:
        return f"<ObraSocial {self.nombre}>"
