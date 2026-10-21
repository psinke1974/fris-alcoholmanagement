import pytest

from app import create_app
from app.config import Config
from app.extensions import db


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


@pytest.fixture(autouse=True)
def reset_throttles():
    """De inlog- en demo-rem zijn globaal per proces; laat ze niet tussen tests doorlekken."""
    from app.blueprints.auth.routes import demo_throttle
    from app.security import login_throttle

    for throttle in (login_throttle, demo_throttle):
        throttle._attempts.clear()
    yield


@pytest.fixture
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    client.post("/register", data={
        "username": "testuser",
        "password": "testpass123",
        "password2": "testpass123",
        "accept_privacy": "1",
    }, follow_redirects=True)
    return client
