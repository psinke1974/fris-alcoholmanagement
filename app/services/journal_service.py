"""Dagboek — opslaan en ophalen van journal entries met HTML-sanitisatie."""

import bleach
from datetime import date

from app.extensions import db
from app.models import JournalEntry

ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "s", "h1", "h2", "h3",
    "ul", "ol", "li", "blockquote", "a",
]
ALLOWED_ATTRIBUTES = {"a": ["href", "title", "rel"]}


def sanitize_html(html: str) -> str:
    cleaned = bleach.clean(
        html or "",
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )
    return cleaned.strip()


def is_empty_body(html: str) -> bool:
    text = bleach.clean(html or "", tags=[], strip=True).strip()
    return not text


def get_entries_for_user(user_id: int, limit: int = 50) -> list[JournalEntry]:
    return (
        JournalEntry.query.filter_by(user_id=user_id)
        .order_by(JournalEntry.entry_date.desc(), JournalEntry.updated_at.desc())
        .limit(limit)
        .all()
    )


def get_entry(user_id: int, entry_id: int) -> JournalEntry | None:
    return JournalEntry.query.filter_by(id=entry_id, user_id=user_id).first()


def save_entry(
    user_id: int,
    entry_date: date,
    body_html: str,
    title: str | None = None,
    entry_id: int | None = None,
) -> JournalEntry:
    cleaned = sanitize_html(body_html)
    title_clean = (title or "").strip()[:200] or None

    if entry_id:
        entry = get_entry(user_id, entry_id)
        if not entry:
            raise ValueError("Entry niet gevonden")
        entry.entry_date = entry_date
        entry.title = title_clean
        entry.body_html = cleaned
    else:
        entry = JournalEntry(
            user_id=user_id,
            entry_date=entry_date,
            title=title_clean,
            body_html=cleaned,
        )
        db.session.add(entry)

    db.session.commit()
    return entry


def delete_entry(user_id: int, entry_id: int) -> bool:
    entry = get_entry(user_id, entry_id)
    if not entry:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True
