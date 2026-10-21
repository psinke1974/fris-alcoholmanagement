"""Inzage, export en verwijdering van alle gegevens van een gebruiker (AVG art. 15, 17 en 20)."""

import csv
import io
import json
from datetime import date, datetime, timezone

from flask import current_app

from app.extensions import db
from app.models import DrinkLog, Goal, JournalEntry, Profile, User, WebAuthnCredential

EXPORT_FORMAT_VERSION = 1


def _iso(value) -> str | None:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _drink_items(raw: str | None):
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return raw


def export_user_data(user: User) -> dict:
    """Alle persoonsgegevens van deze gebruiker als JSON-serialiseerbare dict.

    Bewust weggelaten: de wachtwoordhash en de publieke sleutels van passkeys. Die zijn
    beveiligingsgegevens zonder betekenis voor de gebruiker en horen niet in een downloadbestand.
    """
    profile = user.profile
    logs = DrinkLog.query.filter_by(user_id=user.id).order_by(DrinkLog.log_date).all()
    goals = Goal.query.filter_by(user_id=user.id).order_by(Goal.created_at).all()
    entries = JournalEntry.query.filter_by(user_id=user.id).order_by(JournalEntry.entry_date).all()

    return {
        "export": {
            "app": current_app.config["SITE_NAME"],
            "format_version": EXPORT_FORMAT_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "account": {
            "username": user.username,
            "created_at": _iso(user.created_at),
            "gap_prompt_dismissed_until": _iso(user.gap_prompt_dismissed_until),
        },
        "profile": {
            "email": profile.email if profile else None,
            "age": profile.age if profile else None,
            "gender": profile.gender if profile else None,
            "education": profile.education if profile else None,
            "country": profile.country if profile else None,
        },
        "passkeys": [
            {"device_name": cred.device_name, "created_at": _iso(cred.created_at)}
            for cred in user.credentials
        ],
        "drink_logs": [
            {
                "date": _iso(log.log_date),
                "units": log.units,
                "drink_type": log.drink_type,
                "drink_items": _drink_items(log.drink_items),
                "notes": log.notes,
                "created_at": _iso(log.created_at),
            }
            for log in logs
        ],
        "goals": [
            {
                "goal_type": goal.goal_type,
                "target_value": goal.target_value,
                "start_date": _iso(goal.start_date),
                "end_date": _iso(goal.end_date),
                "active": bool(goal.active),
                "created_at": _iso(goal.created_at),
            }
            for goal in goals
        ],
        "journal_entries": [
            {
                "date": _iso(entry.entry_date),
                "title": entry.title,
                "body_html": entry.body_html,
                "created_at": _iso(entry.created_at),
                "updated_at": _iso(entry.updated_at),
            }
            for entry in entries
        ],
    }


def export_drink_logs_csv(user: User) -> str:
    """Registraties als CSV (voor Excel/LibreOffice). Puntkomma als scheidingsteken, zoals in NL gebruikelijk."""
    logs = DrinkLog.query.filter_by(user_id=user.id).order_by(DrinkLog.log_date).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["datum", "standaardglazen", "drankjes", "notitie"])
    for log in logs:
        writer.writerow([
            log.log_date.isoformat(),
            f"{log.units:g}".replace(".", ","),
            _csv_safe(log.drink_type or ""),
            _csv_safe(log.notes or ""),
        ])
    return buffer.getvalue()


def _csv_safe(value: str) -> str:
    """Voorkom formule-injectie als het bestand in een spreadsheet wordt geopend."""
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def delete_user_account(user: User) -> None:
    """Verwijder de gebruiker en alles wat aan het account hangt, in één transactie.

    Er wordt expliciet per tabel verwijderd in plaats van alleen op de ORM-cascade te vertrouwen,
    zodat er ook geen rijen achterblijven die niet (meer) in een relatie geladen zijn.
    """
    user_id = user.id
    for model in (JournalEntry, Goal, DrinkLog, WebAuthnCredential, Profile):
        model.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    db.session.delete(user)
    db.session.commit()


def count_user_rows(user_id: int) -> int:
    """Aantal rijen dat nog aan dit user_id hangt (gebruikt in tests en als controle)."""
    total = 0
    for model in (JournalEntry, Goal, DrinkLog, WebAuthnCredential, Profile):
        total += model.query.filter_by(user_id=user_id).count()
    total += User.query.filter_by(id=user_id).count()
    return total
