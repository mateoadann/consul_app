from app.extensions import db
from app.models.base import TimestampMixin


class Profesional(TimestampMixin, db.Model):
    __tablename__ = "profesionales"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    especialidad = db.Column(db.String(100), nullable=True)
    telefono = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, unique=True)

    user = db.relationship("User", back_populates="profesional")
    consultorios = db.relationship(
        "Consultorio",
        secondary="profesional_consultorio",
        back_populates="profesionales",
    )

    turnos = db.relationship("Turno", back_populates="profesional", lazy="dynamic")

    @property
    def nombre_completo(self) -> str:
        return f"{self.apellido}, {self.nombre}"

    def __repr__(self) -> str:
        return f"<Profesional {self.apellido}, {self.nombre}>"
