"""Bepaal de huidige fase bij stoppen met alcohol en lever fase-inhoud."""

from datetime import date

from app.data.cessation_phases import PHASE_CONTENT, PHASE_ORDER, REDUCTION_PHASE_CONTENT
from app.models import DrinkLog, Goal
from app.services.badges_service import days_since_last_drink


def get_phase_key(days: int) -> str:
    if days <= 0:
        return "voorbereiding"
    if days <= 3:
        return "dag_1_3"
    if days <= 7:
        return "week_1"
    if days <= 30:
        return "week_2_4"
    if days <= 90:
        return "maand_1_3"
    return "langdurig"


def get_phase_progress(phase_key: str) -> dict:
    """Voortgang binnen de huidige fase (0–100%) en volgende fase."""
    idx = PHASE_ORDER.index(phase_key) if phase_key in PHASE_ORDER else 0
    next_key = PHASE_ORDER[idx + 1] if idx + 1 < len(PHASE_ORDER) else None
    return {
        "current_index": idx,
        "total_phases": len(PHASE_ORDER),
        "next_phase_key": next_key,
        "next_phase_label": PHASE_CONTENT[next_key]["label"] if next_key else None,
    }


def get_cessation_guidance(
    goals: list[Goal],
    logs: list[DrinkLog],
    since_date: date,
) -> dict | None:
    """
    Retourneert fase-inhoud voor stoppen/minder drinken.
    None als er geen relevant doel is en gebruiker recent gedronken heeft.
    """
    active_goal = next((g for g in goals if g.active), None)
    days = days_since_last_drink(logs, since_date)

    if active_goal and active_goal.goal_type == "abstain":
        phase_key = get_phase_key(days)
        content = PHASE_CONTENT[phase_key]
        progress = get_phase_progress(phase_key)
        return {
            "mode": "abstain",
            "phase_key": phase_key,
            "label": content["label"],
            "description": content["description"],
            "days_since_last_drink": days,
            "tips": content["tips"],
            "positive_effects": content["positive_effects"],
            "negative_effects": content["negative_effects"],
            "progress": progress,
            "all_phases": [
                {"key": key, "label": PHASE_CONTENT[key]["label"]}
                for key in PHASE_ORDER
            ],
        }

    if active_goal and active_goal.goal_type in ("weekly_units", "dry_days"):
        return {
            "mode": "reduction",
            "phase_key": "reduction",
            "label": REDUCTION_PHASE_CONTENT["label"],
            "description": REDUCTION_PHASE_CONTENT["description"],
            "days_since_last_drink": days,
            "tips": REDUCTION_PHASE_CONTENT["tips"],
            "positive_effects": REDUCTION_PHASE_CONTENT["positive_effects"],
            "negative_effects": REDUCTION_PHASE_CONTENT["negative_effects"],
            "progress": None,
            "all_phases": None,
        }

    if days >= 1:
        phase_key = get_phase_key(days)
        content = PHASE_CONTENT[phase_key]
        progress = get_phase_progress(phase_key)
        return {
            "mode": "tracking",
            "phase_key": phase_key,
            "label": content["label"],
            "description": content["description"],
            "days_since_last_drink": days,
            "tips": content["tips"],
            "positive_effects": content["positive_effects"],
            "negative_effects": content["negative_effects"],
            "progress": progress,
            "all_phases": [
                {"key": key, "label": PHASE_CONTENT[key]["label"]}
                for key in PHASE_ORDER
            ],
        }

    return {
        "mode": "voorbereiding",
        "phase_key": "voorbereiding",
        "label": PHASE_CONTENT["voorbereiding"]["label"],
        "description": PHASE_CONTENT["voorbereiding"]["description"],
        "days_since_last_drink": days,
        "tips": PHASE_CONTENT["voorbereiding"]["tips"],
        "positive_effects": PHASE_CONTENT["voorbereiding"]["positive_effects"],
        "negative_effects": PHASE_CONTENT["voorbereiding"]["negative_effects"],
        "progress": get_phase_progress("voorbereiding"),
        "all_phases": [
            {"key": key, "label": PHASE_CONTENT[key]["label"]}
            for key in PHASE_ORDER
        ],
    }
