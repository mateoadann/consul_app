from app.models.app_config import AppConfig
from app.models.audit import TurnoAudit, register_turno_audit_listeners
from app.models.consultorio import Consultorio, profesional_consultorio
from app.models.obra_social import ObraSocial
from app.models.paciente import Paciente
from app.models.profesional import Profesional
from app.models.turno import Turno
from app.models.turno_serie_log import TurnoSerieLog
from app.models.user import User


register_turno_audit_listeners(Turno)

__all__ = [
    "AppConfig",
    "User",
    "Paciente",
    "Profesional",
    "Consultorio",
    "ObraSocial",
    "Turno",
    "TurnoSerieLog",
    "TurnoAudit",
    "profesional_consultorio",
]
