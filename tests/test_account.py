import csv
import io
import json
from datetime import date

from app.extensions import db
from app.models import DrinkLog, Goal, JournalEntry, Profile, User, WebAuthnCredential
from app.services.account_service import count_user_rows


def _fill_account(app):
    # Bewust zonder eigen app_context: zo zien de requests dezelfde sessie en geen verouderde objecten.
    user = User.query.filter_by(username="testuser").first()
    user.profile.email = "test@example.com"
    user.profile.age = 40
    db.session.add(DrinkLog(user_id=user.id, log_date=date(2026, 7, 1), units=2.0,
                            drink_type="2× Standaard bier",
                            drink_items=json.dumps([{"id": "bier", "count": 2}]),
                            notes="=HYPERLINK(\"x\")"))
    db.session.add(DrinkLog(user_id=user.id, log_date=date(2026, 7, 2), units=0.0))
    db.session.add(Goal(user_id=user.id, goal_type="weekly_units", target_value=7))
    db.session.add(JournalEntry(user_id=user.id, entry_date=date(2026, 7, 2),
                                title="Dag 2", body_html="<p>Goed gegaan</p>"))
    db.session.add(WebAuthnCredential(user_id=user.id, credential_id=b"cred-1",
                                      public_key=b"geheime-sleutel", device_name="Telefoon"))
    db.session.commit()
    return user.id


def _register_other(client):
    client.post("/logout")
    client.post("/register", data={
        "username": "anderegebruiker",
        "password": "anderwachtwoord",
        "password2": "anderwachtwoord",
        "accept_privacy": "1",
    })


def test_profile_links_to_export_and_delete(auth_client):
    response = auth_client.get("/profile")
    assert b"/account/export.json" in response.data
    assert b"/account/export.csv" in response.data
    assert b"/account/verwijderen" in response.data


def test_export_requires_login(client):
    for path in ("/account/export.json", "/account/export.csv", "/account/verwijderen"):
        response = client.get(path)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


def test_export_json_contains_all_user_data(auth_client, app):
    _fill_account(app)
    response = auth_client.get("/account/export.json")
    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert "attachment" in response.headers["Content-Disposition"]
    assert response.headers["Cache-Control"] == "no-store"

    data = json.loads(response.data)
    assert data["account"]["username"] == "testuser"
    assert data["profile"]["email"] == "test@example.com"
    assert data["profile"]["age"] == 40
    assert [log["date"] for log in data["drink_logs"]] == ["2026-07-01", "2026-07-02"]
    assert data["drink_logs"][0]["drink_items"] == [{"id": "bier", "count": 2}]
    assert data["goals"][0]["goal_type"] == "weekly_units"
    assert data["journal_entries"][0]["body_html"] == "<p>Goed gegaan</p>"
    assert data["passkeys"] == [{"device_name": "Telefoon", "created_at": data["passkeys"][0]["created_at"]}]


def test_export_json_leaves_out_secrets(auth_client, app):
    _fill_account(app)
    body = auth_client.get("/account/export.json").data
    assert b"password" not in body
    assert b"geheime-sleutel" not in body
    assert b"public_key" not in body


def test_export_only_contains_own_data(auth_client, app):
    _fill_account(app)
    _register_other(auth_client)
    data = json.loads(auth_client.get("/account/export.json").data)
    assert data["account"]["username"] == "anderegebruiker"
    assert data["drink_logs"] == []
    assert data["journal_entries"] == []


def test_export_csv(auth_client, app):
    _fill_account(app)
    response = auth_client.get("/account/export.csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    rows = list(csv.reader(io.StringIO(response.data.decode("utf-8-sig")), delimiter=";"))
    assert rows[0] == ["datum", "standaardglazen", "drankjes", "notitie"]
    assert rows[1][:3] == ["2026-07-01", "2", "2× Standaard bier"]
    # Formule-injectie wordt onschadelijk gemaakt.
    assert rows[1][3].startswith("'=")
    assert rows[2][:2] == ["2026-07-02", "0"]


def test_delete_account_requires_password(auth_client, app):
    user_id = _fill_account(app)
    response = auth_client.post("/account/verwijderen", data={"password": "fout", "confirm": "1"})
    assert response.status_code == 400
    assert b"Onjuist wachtwoord" in response.data
    with app.app_context():
        assert db.session.get(User, user_id) is not None


def test_delete_account_requires_confirmation(auth_client, app):
    user_id = _fill_account(app)
    response = auth_client.post("/account/verwijderen", data={"password": "testpass123"})
    assert response.status_code == 400
    with app.app_context():
        assert db.session.get(User, user_id) is not None


def test_delete_account_removes_everything(auth_client, app):
    user_id = _fill_account(app)
    response = auth_client.post("/account/verwijderen", data={"password": "testpass123", "confirm": "1"})
    assert response.status_code == 302
    assert response.headers["Clear-Site-Data"] == '"cache", "storage"'

    with app.app_context():
        assert count_user_rows(user_id) == 0
        for model in (Profile, DrinkLog, Goal, JournalEntry, WebAuthnCredential):
            assert model.query.count() == 0

    # Uitgelogd, en inloggen met het oude account lukt niet meer.
    assert auth_client.get("/dashboard").status_code == 302
    login = auth_client.post("/login", data={"username": "testuser", "password": "testpass123"})
    assert b"Onjuiste gebruikersnaam" in login.data


def test_delete_account_leaves_other_users_alone(auth_client, app):
    _fill_account(app)
    _register_other(auth_client)
    auth_client.post("/account/verwijderen", data={"password": "anderwachtwoord", "confirm": "1"})
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user is not None
        assert DrinkLog.query.filter_by(user_id=user.id).count() == 2
        assert User.query.filter_by(username="anderegebruiker").first() is None


def test_delete_account_is_throttled(auth_client, app):
    app.config["LOGIN_MAX_ATTEMPTS"] = 2
    for _ in range(2):
        auth_client.post("/account/verwijderen", data={"password": "fout", "confirm": "1"})
    response = auth_client.post("/account/verwijderen", data={"password": "testpass123", "confirm": "1"})
    assert response.status_code == 429
    with app.app_context():
        assert User.query.filter_by(username="testuser").first() is not None
