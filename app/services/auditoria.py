from app.models import TurnoAudit


def get_audit_logs(page: int = 1, per_page: int = 30):
    return (
        TurnoAudit.query.order_by(TurnoAudit.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
