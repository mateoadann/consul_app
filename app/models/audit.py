from sqlalchemy import event, inspect
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import object_session

from app.extensions import db
from app.models.base import TimestampMixin


class TurnoAudit(TimestampMixin, db.Model):
    __tablename__ = "turnos_audit"

    id = db.Column(db.Integer, primary_key=True)
    turno_id = db.Column(db.Integer, db.ForeignKey("turnos.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    accion = db.Column(db.String(50), nullable=False)
    campo_modificado = db.Column(db.String(50), nullable=True)
    valor_anterior = db.Column(db.Text, nullable=True)
    valor_nuevo = db.Column(db.Text, nullable=True)
    ip_address = db.Column(INET, nullable=True)

    def __repr__(self) -> str:
        return f"<TurnoAudit {self.turno_id} {self.accion}>"


def _audit_metadata(target):
    session = object_session(target)
    if not session:
        return None, None
    return session.info.get("audit_user_id"), session.info.get("audit_ip")


def _insert_audit(connection, turno_id, user_id, ip_address, accion, campo=None, before=None, after=None):
    connection.execute(
        TurnoAudit.__table__.insert().values(
            turno_id=turno_id,
            user_id=user_id,
            accion=accion,
            campo_modificado=campo,
            valor_anterior=str(before) if before is not None else None,
            valor_nuevo=str(after) if after is not None else None,
            ip_address=ip_address,
        )
    )


def register_turno_audit_listeners(turno_model):
    @event.listens_for(turno_model, "after_insert")
    def on_turno_insert(_mapper, connection, target):
        user_id, ip = _audit_metadata(target)
        _insert_audit(connection, target.id, user_id, ip, "turno_creado")

    @event.listens_for(turno_model, "after_update")
    def on_turno_update(_mapper, connection, target):
        user_id, ip = _audit_metadata(target)
        state = inspect(target)

        tracked_fields = {
            "estado",
            "profesional_id",
            "consultorio_id",
            "paciente_id",
            "durante",
            "motivo_cancelacion",
        }

        for field in tracked_fields:
            history = state.attrs[field].history
            if not history.has_changes():
                continue

            before = history.deleted[0] if history.deleted else None
            after = history.added[0] if history.added else None

            _insert_audit(
                connection,
                target.id,
                user_id,
                ip,
                accion="turno_actualizado",
                campo=field,
                before=before,
                after=after,
            )
