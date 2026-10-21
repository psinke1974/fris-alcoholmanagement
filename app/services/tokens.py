import hashlib
import hmac

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from flask import current_app

from app.extensions import db

PASSWORD_RESET_SALT = "password-reset"
PASSWORD_RESET_MAX_AGE = 3600  # 1 uur


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def _password_fingerprint(user) -> str:
    """Korte afgeleide van de wachtwoordhash: na een wachtwoordwijziging wordt de token ongeldig."""
    return hashlib.sha256(user.password_hash.encode()).hexdigest()[:16]


def generate_password_reset_token(user) -> str:
    return _serializer().dumps(
        {"uid": user.id, "pw": _password_fingerprint(user)}, salt=PASSWORD_RESET_SALT
    )


def verify_password_reset_token(token: str):
    """Geeft de User terug als de token geldig, niet verlopen en nog niet gebruikt is."""
    from app.models import User

    try:
        data = _serializer().loads(token, salt=PASSWORD_RESET_SALT, max_age=PASSWORD_RESET_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("uid"), int):
        return None

    user = db.session.get(User, data["uid"])
    if not user or not hmac.compare_digest(str(data.get("pw", "")), _password_fingerprint(user)):
        return None
    return user
