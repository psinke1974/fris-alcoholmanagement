from app.models import Profile, User
from app.services.tokens import generate_password_reset_token, verify_password_reset_token


def test_profile_save_email(auth_client, app):
    response = auth_client.post("/profile", data={
        "email": "test@example.com",
        "age": "30",
        "gender": "man",
        "education": "hbo",
        "country": "Nederland",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Profiel opgeslagen" in response.data

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user.profile.email == "test@example.com"


def test_forgot_password_sends_link(auth_client, app):
    auth_client.post("/logout")
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        user.profile.email = "reset@example.com"
        from app.extensions import db
        db.session.commit()

    response = auth_client.post("/wachtwoord-vergeten", data={
        "email": "reset@example.com",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"resetlink" in response.data.lower()


def test_password_reset_flow(auth_client, app):
    auth_client.post("/logout")
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        user.profile.email = "reset@example.com"
        from app.extensions import db
        db.session.commit()
        token = generate_password_reset_token(user)

    response = auth_client.post(f"/wachtwoord-reset/{token}", data={
        "password": "nieuwwachtwoord",
        "password2": "nieuwwachtwoord",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"gewijzigd" in response.data.lower()

    login_response = auth_client.post("/login", data={
        "username": "testuser",
        "password": "nieuwwachtwoord",
    }, follow_redirects=True)
    assert login_response.status_code == 200


def test_password_reset_invalid_token(client):
    response = client.get("/wachtwoord-reset/ongeldig-token", follow_redirects=True)
    assert response.status_code == 200
    assert b"ongeldig" in response.data.lower() or b"verlopen" in response.data.lower()


def test_passkey_register_begin(auth_client):
    response = auth_client.post("/passkey/register/begin")
    assert response.status_code == 200
    data = response.get_json()
    assert "challenge" in data
    assert "rp" in data
