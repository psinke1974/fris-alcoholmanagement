"""Eenvoudige SQLite-migraties bij opstarten."""

from sqlalchemy import inspect, text

from app.extensions import db


def apply_pending_migrations() -> None:
    """Voer ontbrekende kolommen/tabellen toe op bestaande databases."""
    inspector = inspect(db.engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    if "gap_prompt_dismissed_until" not in columns:
        db.session.execute(text("ALTER TABLE users ADD COLUMN gap_prompt_dismissed_until DATE"))
        db.session.commit()

    if "drink_logs" in inspector.get_table_names():
        log_columns = {col["name"] for col in inspector.get_columns("drink_logs")}
        if "drink_items" not in log_columns:
            db.session.execute(text("ALTER TABLE drink_logs ADD COLUMN drink_items TEXT"))
            db.session.commit()
