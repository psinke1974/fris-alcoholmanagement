import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project root (één niveau boven app/)
BASE_DIR = Path(__file__).resolve().parent.parent


# Alleen bedoeld voor lokale ontwikkeling. Buiten debug/testing weigert de app te starten met deze waarde.
DEV_SECRET_KEY = "dev-only-change-in-production"


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", DEV_SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'minder_drinken.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cookies: zet SESSION_COOKIE_SECURE=true zodra de app via HTTPS draait.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    WTF_CSRF_ENABLED = True

    # Maximale grootte van een request (dagboek-HTML e.d.)
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024

    # Achter een reverse proxy (nginx, Caddy): aantal vertrouwde proxies voor X-Forwarded-*
    TRUSTED_PROXIES = int(os.environ.get("TRUSTED_PROXIES", "0"))

    # Eenvoudige rem op inlogpogingen (in-memory, per proces)
    LOGIN_MAX_ATTEMPTS = int(os.environ.get("LOGIN_MAX_ATTEMPTS", "10"))
    LOGIN_WINDOW_SECONDS = int(os.environ.get("LOGIN_WINDOW_SECONDS", "900"))

    SITE_NAME = os.environ.get("SITE_NAME", "Fris")
    SITE_TAGLINE = os.environ.get(
        "SITE_TAGLINE",
        "Houd je alcoholgebruik bij en werk in je eigen tempo aan minderen of stoppen.",
    )
    CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "contact@example.org")

    WEBAUTHN_RP_ID = os.environ.get("WEBAUTHN_RP_ID", "localhost")
    WEBAUTHN_RP_NAME = os.environ.get("WEBAUTHN_RP_NAME", SITE_NAME)
    WEBAUTHN_ORIGIN = os.environ.get("WEBAUTHN_ORIGIN", "http://localhost:8080")

    # Richtlijn: max 14 eenheden/week (mannen), 7 (vrouwen) — Trimbos/RIVM
    DEFAULT_WEEKLY_LIMIT = 14

    # E-mail (optioneel — zonder SMTP worden mails naar de log geschreven)
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@example.org")
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ("1", "true", "yes")
