from functools import wraps

from flask import abort, request
from flask_login import current_user


def role_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def htmx_request() -> bool:
    return request.headers.get("HX-Request", "").lower().strip() == "true"
