import json
from datetime import date, timedelta


def test_index_shows_landing(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Gratis beginnen" in response.data
    assert b"Helder" in response.data


def test_privacy_and_partners_pages(client):
    privacy = client.get("/privacy")
    assert privacy.status_code == 200
    assert b"Privacyverklaring" in privacy.data

    about = client.get("/over")
    assert about.status_code == 200
    assert b"Over" in about.data

    partners = client.get("/partners")
    assert partners.status_code == 200
    assert b"Samenwerking" in partners.data


def test_manifest_available(client):
    response = client.get("/static/manifest.webmanifest")
    assert response.status_code == 200
    assert b"standalone" in response.data


def test_register_and_dashboard(auth_client):
    response = auth_client.get("/dashboard")
    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_log_drink(auth_client):
    drink_items = json.dumps([{"id": "tripel", "count": 1}, {"id": "bier", "count": 1}])
    auth_client.post("/log", data={
        "log_date": "2026-07-06",
        "drink_items": drink_items,
    }, follow_redirects=True)

    response = auth_client.get("/dashboard")
    assert b"2.6" in response.data or b"2,6" in response.data


def test_log_page_shows_existing_registration(auth_client):
    drink_items = json.dumps([{"id": "tripel", "count": 2}])
    auth_client.post("/log", data={
        "log_date": "2026-07-05",
        "drink_items": drink_items,
    }, follow_redirects=True)

    response = auth_client.get("/log")
    assert response.status_code == 200
    assert b'"2026-07-05"' in response.data
    assert b'"tripel"' in response.data
    assert b'"count": 2' in response.data
    assert b'"registered": true' in response.data
    assert b'"zero": false' in response.data


def test_log_page_shows_zero_day_registration(auth_client):
    auth_client.post("/log", data={
        "log_date": "2026-07-04",
        "drink_items": "[]",
    }, follow_redirects=True)

    response = auth_client.get("/log")
    assert response.status_code == 200
    assert b'"2026-07-04"' in response.data
    assert b'"zero": true' in response.data
    assert b'log-status' in response.data


def test_log_zero_alcohol(auth_client):
    auth_client.post("/log", data={
        "log_date": "2026-07-06",
        "drink_items": "[]",
    }, follow_redirects=True)

    response = auth_client.get("/dashboard")
    assert response.status_code == 200


def test_profile_page(auth_client):
    response = auth_client.get("/profile")
    assert response.status_code == 200
    assert b"Profiel" in response.data


def test_catch_up_redirects_without_gap(auth_client):
    auth_client.post("/log", data={
        "log_date": date.today().isoformat(),
        "drink_items": "[]",
    }, follow_redirects=True)
    response = auth_client.get("/catch-up")
    assert response.status_code == 302
    assert "/dashboard" in response.location


def test_catch_up_shows_gap(auth_client):
    old = (date.today() - timedelta(days=5)).isoformat()
    auth_client.post("/log", data={"log_date": old, "drink_items": "[]"})
    response = auth_client.get("/catch-up")
    assert response.status_code == 200
    assert b"Inhaalmodus" in response.data


def test_catch_up_dry_all(auth_client):
    old = (date.today() - timedelta(days=5)).isoformat()
    auth_client.post("/log", data={"log_date": old, "drink_items": "[]"})
    gap_start = (date.today() - timedelta(days=4)).isoformat()
    gap_end = (date.today() - timedelta(days=1)).isoformat()
    auth_client.post("/catch-up", data={
        "action": "dry_all",
        "gap_start": gap_start,
        "gap_end": gap_end,
    }, follow_redirects=True)
    response = auth_client.get("/dashboard")
    assert response.status_code == 200
    assert b"niet geregistreerd" not in response.data
