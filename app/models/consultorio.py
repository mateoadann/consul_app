from app.extensions import db
from app.models.base import TimestampMixin


DEFAULT_CONSULTORIO_COLOR = "#EA8711"
CONSULTORIO_COLOR_CLASS_MAP = {
    "#EA8711": "cc-naranja",
    "#0D9488": "cc-turquesa",
    "#2563EB": "cc-azul",
    "#16A34A": "cc-verde",
    "#DC2626": "cc-rojo",
    "#7C3AED": "cc-violeta",
    "#C2410C": "cc-terracota",
    "#0891B2": "cc-cian",
    "#BE123C": "cc-frambuesa",
    "#4F46E5": "cc-indigo",
}


profesional_consultorio = db.Table(
    "profesional_consultorio",
    db.Column(
        "profesional_id",
        db.Integer,
        db.ForeignKey("profesionales.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "consultorio_id",
        db.Integer,
        db.ForeignKey("consultorios.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Consultorio(TimestampMixin, db.Model):
    __tablename__ = "consultorios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7), nullable=False, default="#EA8711")
    activo = db.Column(db.Boolean, nullable=False, default=True)

    profesionales = db.relationship(
        "Profesional",
        secondary=profesional_consultorio,
        back_populates="consultorios",
    )
    turnos = db.relationship("Turno", back_populates="consultorio", lazy="dynamic")

    @property
    def color_normalized(self) -> str:
        return (self.color or DEFAULT_CONSULTORIO_COLOR).upper()

    @property
    def color_class(self) -> str:
        return CONSULTORIO_COLOR_CLASS_MAP.get(self.color_normalized, "cc-naranja")

    def __repr__(self) -> str:
        return f"<Consultorio {self.nombre}>"
