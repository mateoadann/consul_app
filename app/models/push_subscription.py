from app.extensions import db
from app.models.base import TimestampMixin


class PushSubscription(TimestampMixin, db.Model):
    __tablename__ = "push_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    endpoint = db.Column(db.Text, nullable=False, unique=True)
    p256dh = db.Column(db.String(256), nullable=False)
    auth = db.Column(db.String(128), nullable=False)

    user = db.relationship("User", back_populates="push_subscriptions")

    def to_push_info(self) -> dict:
        """Return dict in the format pywebpush expects."""
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh,
                "auth": self.auth,
            },
        }

    def __repr__(self) -> str:
        return f"<PushSubscription user_id={self.user_id} id={self.id}>"
