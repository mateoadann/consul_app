from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Index, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint, TSRANGE

from app.extensions import db
from app.models.base import TimestampMixin


class Turno(TimestampMixin, db.Model):
    __tablename__ = "turnos"

    ESTADOS = ("reservado", "confirmado", "atendido", "cancelado")
    TRANSICIONES_VALIDAS = {
        "reservado": {"confirmado", "cancelado"},
        "confirmado": {"atendido", "cancelado"},
        "atendido": set(),
        "cancelado": set(),
    }

    id = db.Column(db.Integer, primary_key=True)

    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False)
    profesional_id = db.Column(db.Integer, db.ForeignKey("profesionales.id"), nullable=False)
    consultorio_id = db.Column(db.Integer, db.ForeignKey("consultorios.id"), nullable=False)

    durante = db.Column(TSRANGE, nullable=False)
    estado = db.Column(
        db.Enum(*ESTADOS, name="turno_estado_enum"),
        nullable=False,
        default="reservado",
        server_default="reservado",
    )

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    cancelado_por = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    cancelado_at = db.Column(db.DateTime(timezone=True), nullable=True)
    motivo_cancelacion = db.Column(db.Text, nullable=True)

    paciente = db.relationship("Paciente", back_populates="turnos")
    profesional = db.relationship("Profesional", back_populates="turnos")
    consultorio = db.relationship("Consultorio", back_populates="turnos")

    creador = db.relationship("User", foreign_keys=[created_by])
    cancelador = db.relationship("User", foreign_keys=[cancelado_por])

    __table_args__ = (
        ExcludeConstraint(
            ("consultorio_id", "="),
            ("durante", "&&"),
            where=text("estado != 'cancelado'"),
            using="gist",
            name="no_solapamiento_consultorio",
        ),
        ExcludeConstraint(
            ("profesional_id", "="),
            ("durante", "&&"),
            where=text("estado != 'cancelado'"),
            using="gist",
            name="no_solapamiento_profesional",
        ),
        ExcludeConstraint(
            ("paciente_id", "="),
            ("durante", "&&"),
            where=text("estado != 'cancelado'"),
            using="gist",
            name="no_solapamiento_paciente",
        ),
        CheckConstraint(
            "upper(durante) - lower(durante) >= interval '15 minutes'"
            " AND upper(durante) - lower(durante) <= interval '120 minutes'",
            name="duracion_valida",
        ),
        Index("ix_turnos_durante_gist", "durante", postgresql_using="gist"),
        Index("ix_turnos_consultorio_fecha", "consultorio_id", text("(lower(durante)::date)")),
        Index("ix_turnos_profesional_fecha", "profesional_id", text("(lower(durante)::date)")),
    )

    @property
    def start_at(self):
        return self.durante.lower if self.durante else None

    @property
    def end_at(self):
        return self.durante.upper if self.durante else None

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.TRANSICIONES_VALIDAS.get(self.estado, set())

    def apply_state(self, new_status: str, actor_user_id: int, motivo: str | None = None) -> None:
        if not self.can_transition_to(new_status):
            raise ValueError(f"Transicion invalida: {self.estado} -> {new_status}")

        self.estado = new_status
        if new_status == "cancelado":
            self.cancelado_por = actor_user_id
            self.cancelado_at = datetime.now(timezone.utc)
            self.motivo_cancelacion = motivo

    def __repr__(self) -> str:
        return f"<Turno #{self.id} {self.estado}>"
