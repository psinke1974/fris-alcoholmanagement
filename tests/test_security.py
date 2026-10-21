import pytest

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import User
from app.security import login_throttle
from app.services.tokens import generate_password_reset_token


@pytest.fixture(autouse=True)
def _reset_throttle():
    login_throttle._attempts.clear()
    yield
    login_throttle._attempts.clear()


def test_security_headers_present(client):
    response = client.get("/")
    csp = response.headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in csp
    assert "nonce-" in csp
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Cache-Control"] == "no-store"


def test_inline_script_gets_nonce(client):
    response = client.get("/login")
    csp = response.headers["Content-Security-Policy"]
    nonce = csp.split("'nonce-")[1].split("'")[0]
    assert f'nonce="{nonce}"'.encode() in response.data


def test_login_rejects_open_redirect(auth_client):
    auth_client.post("/logout")
    response = auth_client.post("/login?next=https://evil.example/", data={
        "username": "testuser",
        "password": "testpass123",
    })
    assert response.status_code == 302
    assert "evil.example" not in response.headers["Location"]


def test_login_allows_local_next(auth_client):
    auth_client.post("/logout")
    response = auth_client.post("/login?next=/goals", data={
        "username": "testuser",
        "password": "testpass123",
    })
    assert response.headers["Location"].endswith("/goals")


@pytest.mark.parametrize("target", ["//evil.example", "/\\evil.example", "javascript:alert(1)"])
def test_login_rejects_tricky_next(auth_client, target):
    auth_client.post("/logout")
    response = auth_client.post("/login", query_string={"next": target}, data={
        "username": "testuser",
        "password": "testpass123",
    })
    assert "evil.example" not in response.headers["Location"]
    assert not response.headers["Location"].startswith("javascript")


def test_logout_requires_post(auth_client):
    assert auth_client.get("/logout").status_code == 405
    assert auth_client.post("/logout").status_code == 302


def test_login_throttled_after_failures(app, auth_client):
    auth_client.post("/logout")
    for _ in range(app.config["LOGIN_MAX_ATTEMPTS"]):
        auth_client.post("/login", data={"username": "testuser", "password": "fout"})
    response = auth_client.post("/login", data={"username": "testuser", "password": "testpass123"})
    assert response.status_code == 429


def test_reset_token_single_use(auth_client, app):
    auth_client.post("/logout")
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        token = generate_password_reset_token(user)

    data = {"password": "nieuwwachtwoord", "password2": "nieuwwachtwoord"}
    auth_client.post(f"/wachtwoord-reset/{token}", data=data)
    response = auth_client.post(f"/wachtwoord-reset/{token}", data={
        "password": "nogeenwachtwoord", "password2": "nogeenwachtwoord",
    }, follow_redirects=True)
    assert b"ongeldig of verlopen" in response.data


def test_goal_rejects_unknown_type(auth_client):
    response = auth_client.post("/goals", data={"goal_type": "hack", "target_value": "3"}, follow_redirects=True)
    assert b"Onbekend type doel" in response.data


def test_goal_rejects_out_of_range(auth_client):
    response = auth_client.post("/goals", data={"goal_type": "dry_days", "target_value": "12"}, follow_redirects=True)
    assert b"tussen 0 en 7" in response.data


def test_missing_secret_key_refused_in_production(monkeypatch):
    class ProdConfig(Config):
        SECRET_KEY = "dev-only-change-in-production"
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    with pytest.raises(RuntimeError):
        create_app(ProdConfig)


def test_passkey_login_complete_rejects_bad_payload(client):
    client.post("/passkey/login/begin", json={})
    response = client.post("/passkey/login/complete", json={"rawId": 123})
    assert response.status_code == 400
