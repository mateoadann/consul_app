from sqlalchemy.sql import func

from app.extensions import db


class NotificationLog(db.Model):
    __tablename__ = "notification_logs"
    __table_args__ = (
        db.UniqueConstraint(
            "paciente_id", "notification_type", "year",
            name="uq_notification_log_unique",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False)
    notification_type = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    sent_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

    paciente = db.relationship("Paciente")

    def __repr__(self) -> str:
        return f"<NotificationLog paciente_id={self.paciente_id} type={self.notification_type} year={self.year}>"
