"""Berekening en weergave van drankregistraties."""

import json

from app.constants import DRINK_OPTIONS, DRINK_OPTIONS_BY_ID
from app.models.drink import DrinkLog


def parse_drink_items(raw: str) -> list[dict]:
    try:
        data = json.loads(raw or "[]")
    except (json.JSONDecodeError, TypeError):
        return []

    if not isinstance(data, list):
        return []

    items = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        drink_id = entry.get("id")
        count = entry.get("count", 0)
        if drink_id not in DRINK_OPTIONS_BY_ID:
            continue
        try:
            count = int(count)
        except (TypeError, ValueError):
            continue
        if count > 0:
            items.append({"id": drink_id, "count": count})
    return items


def calculate_units_from_items(items: list[dict]) -> float:
    total = 0.0
    for entry in items:
        drink = DRINK_OPTIONS_BY_ID[entry["id"]]
        total += drink["units"] * entry["count"]
    return round(total, 1)


def format_drink_summary(items: list[dict]) -> str:
    parts = []
    for entry in items:
        drink = DRINK_OPTIONS_BY_ID[entry["id"]]
        count = entry["count"]
        label = drink["label"]
        if count == 1:
            parts.append(label)
        else:
            parts.append(f"{count}× {label}")
    return ", ".join(parts)


def serialize_drink_items(items: list[dict]) -> str | None:
    if not items:
        return None
    return json.dumps(items)


def parse_drink_summary(summary: str) -> list[dict]:
    """Herstel drankjes uit de opgeslagen samenvatting (oudere registraties)."""
    if not summary:
        return []

    labels = sorted(
        ((d["id"], d["label"]) for d in DRINK_OPTIONS),
        key=lambda pair: len(pair[1]),
        reverse=True,
    )
    items = []
    for part in summary.split(", "):
        part = part.strip()
        if not part:
            continue
        for drink_id, label in labels:
            suffix = f"× {label}"
            if part == label:
                items.append({"id": drink_id, "count": 1})
                break
            if part.endswith(suffix):
                count_str = part[: -len(suffix)].strip()
                try:
                    count = int(count_str)
                except ValueError:
                    continue
                if count > 0:
                    items.append({"id": drink_id, "count": count})
                break
    return items


def get_drink_items_for_log(log: DrinkLog) -> list[dict]:
    if log.drink_items:
        return parse_drink_items(log.drink_items)
    if log.drink_type:
        return parse_drink_summary(log.drink_type)
    return []


def log_entry_for_client(log: DrinkLog) -> dict:
    items = get_drink_items_for_log(log)
    is_zero = log.units == 0 and not items
    return {
        "registered": True,
        "items": items,
        "zero": is_zero,
        "units": log.units,
        "notes": log.notes or "",
    }
