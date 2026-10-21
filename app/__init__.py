from flask import Flask

from app.blueprints.auth import auth_bp
from app.blueprints.main import main_bp
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import BASE_DIR, DEV_SECRET_KEY, Config
from app.extensions import csrf, db, login_manager
from app.models import User
from app.security import init_security
from app.services.demo_service import is_expired, purge_demo_users


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    if app.config["SECRET_KEY"] in (None, "", DEV_SECRET_KEY) and not (app.debug or app.testing):
        raise RuntimeError(
            "SECRET_KEY is niet ingesteld. Zet een lange willekeurige waarde in de omgeving "
            "(bijv. via .env) voordat je de app buiten development draait."
        )

    proxies = app.config.get("TRUSTED_PROXIES", 0)
    if proxies:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxies, x_proto=proxies, x_host=proxies)

    data_dir = BASE_DIR / "data"
    data_dir.mkdir(exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Log in om verder te gaan."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        user = db.session.get(User, int(user_id))
        if user is not None and is_expired(user):
            return None
        return user

    init_security(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.context_processor
    def inject_site():
        return {
            "site_name": app.config["SITE_NAME"],
            "site_tagline": app.config["SITE_TAGLINE"],
            "contact_email": app.config["CONTACT_EMAIL"],
            "demo_mode": app.config["DEMO_MODE"],
            "demo_ttl_hours": app.config["DEMO_ACCOUNT_TTL_HOURS"],
        }

    if app.config["DEMO_MODE"]:
        @app.before_request
        def purge_expired_demo_accounts():
            purge_demo_users()

    with app.app_context():
        db.create_all()
        from app.migrate import apply_pending_migrations
        apply_pending_migrations()
        if app.config["DEMO_MODE"]:
            _check_demo_database()

    return app


def _check_demo_database() -> None:
    """Weiger demo-modus op een database met echte accounts: die zouden anders bij de demo horen."""
    if User.query.filter(User.demo_expires_at.is_(None)).first() is not None:
        raise RuntimeError(
            "DEMO_MODE staat aan, maar de database bevat gewone accounts. Gebruik voor de demo "
            "een aparte, lege database (DATABASE_URL) en zet DEMO_MODE nooit aan op een "
            "installatie met echte gebruikers."
        )
    purge_demo_users(force=True)
