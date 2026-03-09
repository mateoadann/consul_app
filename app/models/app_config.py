from app.extensions import db


class AppConfig(db.Model):
    __tablename__ = "app_config"

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(255), nullable=False)

    @staticmethod
    def get(key: str, default: str = "") -> str:
        row = AppConfig.query.get(key)
        return row.value if row else default

    @staticmethod
    def set(key: str, value: str) -> None:
        row = AppConfig.query.get(key)
        if row:
            row.value = value
        else:
            row = AppConfig(key=key, value=value)
            db.session.add(row)
