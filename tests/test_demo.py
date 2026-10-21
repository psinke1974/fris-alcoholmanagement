from datetime import datetime, timedelta

import pytest

from app import create_app
from app.extensions import db
from app.models import DrinkLog, Goal, JournalEntry, User
from app.services.demo_service import create_demo_user, purge_demo_users
from tests.conftest import TestConfig


class DemoConfig(TestConfig):
    DEMO_MODE = True
    DEMO_ACCOUNT_TTL_HOURS = 4
    DEMO_MAX_ACCOUNTS = 3
    DEMO_MAX_PER_IP_PER_HOUR = 100


@pytest.fixture
def demo_app():
    application = create_app(DemoConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def demo_client(demo_app):
    return demo_app.test_client()


def test_demo_off_by_default(client):
    assert b"Probeer de demo" not in client.get("/").data
    response = client.post("/demo")
    assert response.status_code == 302
    with client.application.app_context():
        assert User.query.count() == 0


def test_landing_shows_demo_button_and_banner(demo_client):
    response = demo_client.get("/")
    assert b"Probeer de demo" in response.data
    assert b"demo-banner" in response.data


def test_demo_start_creates_seeded_account(demo_client, demo_app):
    response = demo_client.post("/demo")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")

    dashboard = demo_client.get("/dashboard")
    assert dashboard.status_code == 200

    with demo_app.app_context():
        user = User.query.one()
        assert user.username.startswith("demo-")
        assert user.demo_expires_at > datetime.utcnow()
        assert DrinkLog.query.filter_by(user_id=user.id).count() > 40
        assert Goal.query.filter_by(user_id=user.id, active=True).count() == 1
        assert JournalEntry.query.filter_by(user_id=user.id).count() == 3


def test_demo_pages_render(demo_client):
    demo_client.post("/demo")
    for path in ("/dashboard", "/log", "/dagboek", "/goals", "/profile", "/catch-up", "/account/verwijderen"):
        assert demo_client.get(path, follow_redirects=True).status_code == 200, path


def test_registration_and_password_reset_disabled_in_demo(demo_client, demo_app):
    response = demo_client.post("/register", data={
        "username": "echtepersoon",
        "password": "wachtwoord123",
        "password2": "wachtwoord123",
        "accept_privacy": "1",
    })
    assert response.status_code == 302
    assert demo_client.get("/wachtwoord-vergeten").status_code == 302
    with demo_app.app_context():
        assert User.query.count() == 0


def test_demo_account_can_be_deleted_without_password(demo_client, demo_app):
    demo_client.post("/demo")
    response = demo_client.post("/account/verwijderen", data={"confirm": "1"})
    assert response.status_code == 302
    with demo_app.app_context():
        assert User.query.count() == 0
        assert DrinkLog.query.count() == 0


def test_expired_demo_account_is_logged_out_and_purged(demo_client, demo_app):
    demo_client.post("/demo")
    user = User.query.one()
    user.demo_expires_at = datetime.utcnow() - timedelta(minutes=1)
    db.session.commit()

    # Een verlopen demo-account geldt niet meer als ingelogd.
    assert demo_app.login_manager._user_callback(str(user.id)) is None

    with demo_app.app_context():
        assert purge_demo_users(force=True) == 1
        assert User.query.count() == 0
        assert DrinkLog.query.count() == 0


def test_demo_account_limit_removes_oldest(demo_app):
    with demo_app.app_context():
        users = []
        for _ in range(3):
            purge_demo_users(force=True)
            users.append(create_demo_user().username)
        purge_demo_users(force=True)
        remaining = {u.username for u in User.query.all()}
        assert users[0] not in remaining
        assert len(remaining) == 2


def test_demo_start_is_throttled(demo_client, demo_app):
    demo_app.config["DEMO_MAX_PER_IP_PER_HOUR"] = 1
    demo_client.post("/demo")
    demo_client.post("/logout")
    demo_client.post("/demo")
    with demo_app.app_context():
        assert User.query.count() == 1


def test_demo_mode_refuses_database_with_real_accounts(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'echt.db'}"

    class RealConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = db_url

    app = create_app(RealConfig)
    with app.app_context():
        user = User(username="echtegebruiker")
        user.set_password("wachtwoord123")
        db.session.add(user)
        db.session.commit()
        db.session.remove()
        db.engine.dispose()

    class RealDemoConfig(DemoConfig):
        SQLALCHEMY_DATABASE_URI = db_url

    with pytest.raises(RuntimeError, match="DEMO_MODE"):
        create_app(RealDemoConfig)
