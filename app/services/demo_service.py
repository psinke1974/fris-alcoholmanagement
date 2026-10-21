"""Demo-modus: tijdelijke accounts met voorbeeldgegevens voor een openbare demo-omgeving."""

import random
import secrets
import threading
import time
from datetime import date, datetime, timedelta

from flask import current_app

from app.extensions import db
from app.models import DrinkLog, Goal, JournalEntry, Profile, User
from app.services.account_service import delete_user_account
from app.services.drinks_service import calculate_units_from_items, format_drink_summary, serialize_drink_items

DEMO_HISTORY_DAYS = 56

# Drankjes die het voorbeeldaccount op een "drinkdag" kiest, van zwaar naar licht.
_HEAVY_DAYS = [
    [{"id": "bier", "count": 4}],
    [{"id": "wijn", "count": 3}],
    [{"id": "tripel", "count": 2}, {"id": "bier", "count": 1}],
]
_LIGHT_DAYS = [
    [{"id": "bier", "count": 2}],
    [{"id": "wijn", "count": 1}],
    [{"id": "radler", "count": 2}],
    [{"id": "wijn", "count": 2}],
]

_JOURNAL = [
    (
        "Begonnen met bijhouden",
        "<p>Vandaag besloten om eerlijk op te schrijven wat ik drink. "
        "Het viel me op hoe vaak het <strong>gewoon gewoonte</strong> is: even zitten na het werk.</p>",
    ),
    (
        "Verjaardag overleefd",
        "<p>Op het feest twee biertjes en daarna alcoholvrij. Niemand vroeg er iets van.</p>"
        "<ul><li>Vooraf besloten hoeveel</li><li>Water tussendoor</li></ul>",
    ),
    (
        "Beter geslapen",
        "<p>Derde alcoholvrije avond deze week. Ik merk dat ik minder vaak wakker word.</p>",
    ),
]

_purge_lock = threading.Lock()
_last_purge = 0.0
PURGE_INTERVAL_SECONDS = 300


def is_demo_mode() -> bool:
    return bool(current_app.config.get("DEMO_MODE"))


def _day_items(day_index: int, weekday: int, rng: random.Random) -> list[dict]:
    """Voorbeeldpatroon: eerst vaker en meer drinken, de laatste weken duidelijk minder."""
    progress = day_index / DEMO_HISTORY_DAYS  # 0 = acht weken geleden, 1 = vandaag
    weekend = weekday >= 4
    drink_chance = (0.85 if weekend else 0.55) - 0.4 * progress
    if rng.random() > drink_chance:
        return []
    pool = _HEAVY_DAYS if (progress < 0.5 and weekend) else _LIGHT_DAYS
    return [dict(item) for item in rng.choice(pool)]


def create_demo_user() -> User:
    """Maak een nieuw tijdelijk demo-account met acht weken voorbeeldgegevens."""
    ttl = timedelta(hours=current_app.config["DEMO_ACCOUNT_TTL_HOURS"])
    now = datetime.utcnow()
    today = date.today()
    start = today - timedelta(days=DEMO_HISTORY_DAYS)
    rng = random.Random(secrets.randbits(32))

    user = User(
        username=f"demo-{secrets.token_hex(4)}",
        created_at=now - timedelta(days=DEMO_HISTORY_DAYS),
        demo_expires_at=now + ttl,
    )
    # Niemand kent dit wachtwoord: het account is alleen bereikbaar via de demo-sessie.
    user.set_password(secrets.token_urlsafe(32))
    db.session.add(user)
    db.session.add(Profile(user=user, age=44, gender="vrouw", country="Nederland"))

    # De laatste twee dagen blijven leeg, zodat de demo ook "gemiste dagen invullen" laat zien.
    for offset in range(DEMO_HISTORY_DAYS - 2):
        day = start + timedelta(days=offset)
        items = _day_items(offset, day.weekday(), rng)
        db.session.add(DrinkLog(
            user=user,
            log_date=day,
            units=calculate_units_from_items(items) if items else 0.0,
            drink_type=format_drink_summary(items) if items else None,
            drink_items=serialize_drink_items(items),
            created_at=datetime.combine(day, datetime.min.time()) + timedelta(hours=21),
        ))

    db.session.add(Goal(
        user=user,
        goal_type="weekly_units",
        target_value=7,
        start_date=today - timedelta(days=28),
        active=True,
    ))

    for days_ago, (title, body) in zip((50, 30, 6), _JOURNAL):
        moment = now - timedelta(days=days_ago)
        db.session.add(JournalEntry(
            user=user,
            entry_date=moment.date(),
            title=title,
            body_html=body,
            created_at=moment,
            updated_at=moment,
        ))

    db.session.commit()
    return user


def is_expired(user: User) -> bool:
    return user.demo_expires_at is not None and user.demo_expires_at <= datetime.utcnow()


def purge_demo_users(force: bool = False) -> int:
    """Verwijder verlopen demo-accounts, en de oudste als het maximum bereikt is.

    Draait hooguit eens per PURGE_INTERVAL_SECONDS, tenzij force=True.
    """
    global _last_purge
    with _purge_lock:
        if not force and time.monotonic() - _last_purge < PURGE_INTERVAL_SECONDS:
            return 0
        _last_purge = time.monotonic()

    removed = 0
    now = datetime.utcnow()
    for user in User.query.filter(User.demo_expires_at.isnot(None), User.demo_expires_at <= now).all():
        delete_user_account(user)
        removed += 1

    max_accounts = current_app.config["DEMO_MAX_ACCOUNTS"]
    demo_query = User.query.filter(User.demo_expires_at.isnot(None))
    surplus = demo_query.count() - max_accounts + 1  # ruimte voor het account dat nu gemaakt wordt
    if surplus > 0:
        for user in demo_query.order_by(User.demo_expires_at).limit(surplus).all():
            delete_user_account(user)
            removed += 1
    return removed
