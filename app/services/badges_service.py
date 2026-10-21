"""Mijlpaalbadges — geïnspireerd op gangbare sober-trackers (o.a. I Am Sober, recovery-programma's)."""

from datetime import date, timedelta

from app.models import DrinkLog

# Veelgebruikte drempels: 1, 7, 30, 90 dagen; weken op 1, 4, 12, 52
DAY_MILESTONES = [
    (1, "Eerste dag", "Je eerste alcoholvrije dag geregistreerd", "🌱"),
    (3, "3 dagen", "3 opeenvolgende geregistreerde alcoholvrije dagen", "⭐"),
    (7, "Eén week", "7 opeenvolgende geregistreerde dagen zonder alcohol", "🏅"),
    (14, "Twee weken", "14 opeenvolgende geregistreerde dagen — gewoontes beginnen te veranderen", "🎯"),
    (30, "Eén maand", "30 opeenvolgende geregistreerde dagen — je lichaam herstelt merkbaar", "🌿"),
    (60, "Twee maanden", "60 opeenvolgende geregistreerde dagen — stevige basis", "💪"),
    (90, "Drie maanden", "90 opeenvolgende geregistreerde dagen — een solide mijlpaal", "🏆"),
    (180, "Half jaar", "6 maanden aaneengesloten geregistreerd alcoholvrij", "✨"),
    (365, "Eén jaar", "365 opeenvolgende geregistreerde dagen — een jaar vol groei", "👑"),
]

WEEK_MILESTONES = [
    (1, "Eerste week", "Een volledige week zonder alcohol (7 opeenvolgende geregistreerde dagen)", "📅"),
    (2, "Twee weken", "2 opeenvolgende alcoholvrije weken", "📆"),
    (4, "Eén maand", "4 weken op rij — bijna een maand", "🗓️"),
    (8, "Twee maanden", "8 weken zonder een druppel", "🎖️"),
    (12, "Drie maanden", "12 weken — kwartaal gehaald", "🥇"),
    (26, "Half jaar", "26 weken alcoholvrij", "🌟"),
    (52, "Eén jaar", "52 weken — een vol jaar", "💎"),
]


def compute_dry_streak(logs: list[DrinkLog], since_date: date) -> int:
    """Opeenvolgende expliciet geregistreerde alcoholvrije dagen (0 glazen).

    Telt vanaf vandaag terug zolang elke dag is geregistreerd met 0 glazen.
    Een ontbrekende dag of een drinkdag breekt de reeks — kalenderdagen zonder
    registratie tellen niet mee.
    Vandaag telt alleen mee als die al is geregistreerd als 0.
    """
    today = date.today()
    if not logs or today < since_date:
        return 0

    log_by_date = {log.log_date: log.units for log in logs}
    streak = 0
    check = today if today in log_by_date else today - timedelta(days=1)

    while check >= since_date:
        if check not in log_by_date:
            break
        if log_by_date[check] > 0:
            break
        streak += 1
        check -= timedelta(days=1)

    return streak


def days_since_last_drink(logs: list[DrinkLog], since_date: date) -> int:
    """Alias voor mijlpalen/fase: alleen opeenvolgende geregistreerde droge dagen.

    Historisch heette dit 'kalenderdagen sinds laatste drank', maar niet-geregistreerde
    periodes mogen niet als alcoholvrij meetellen. Daarom gelijk aan compute_dry_streak.
    """
    return compute_dry_streak(logs, since_date)


def compute_consecutive_alcohol_free_days(logs: list[DrinkLog], since_date: date) -> int:
    """Opeenvolgende geregistreerde alcoholvrije dagen; stopt bij ontbrekende of drink-dag."""
    return compute_dry_streak(logs, since_date)


def compute_dry_week_streak(logs: list[DrinkLog], since_date: date) -> int:
    """Volle weken = 7 opeenvolgende dagen met expliciet 0 glazen geregistreerd."""
    return compute_consecutive_alcohol_free_days(logs, since_date) // 7


def _build_badges(
    milestones: list[tuple],
    current: int,
    category: str,
    unit: str,
) -> dict:
    earned = []
    locked = []
    next_badge = None

    for threshold, title, description, icon in milestones:
        badge = {
            "id": f"{category}_{threshold}",
            "title": title,
            "description": description,
            "icon": icon,
            "threshold": threshold,
            "category": category,
            "unit": unit,
            "earned": current >= threshold,
        }
        if badge["earned"]:
            earned.append(badge)
        else:
            locked.append(badge)
            if next_badge is None:
                next_badge = {**badge, "remaining": threshold - current, "progress_pct": min(100, int(current / threshold * 100))}

    return {
        "earned": earned,
        "locked": locked,
        "next": next_badge,
        "current": current,
    }


def compute_badges(logs: list[DrinkLog], since_date: date) -> dict:
    consecutive = compute_consecutive_alcohol_free_days(logs, since_date)
    weeks = consecutive // 7

    return {
        "days_since_last_drink": consecutive,
        "dry_streak": consecutive,
        "consecutive_alcohol_free_days": consecutive,
        "dry_week_streak": weeks,
        "days": _build_badges(DAY_MILESTONES, consecutive, "days", "dagen"),
        "weeks": _build_badges(WEEK_MILESTONES, weeks, "weeks", "weken"),
        "recently_earned": _recently_earned(DAY_MILESTONES, WEEK_MILESTONES, consecutive, weeks),
    }


def _recently_earned(day_ms, week_ms, days, weeks) -> list[dict]:
    """Badges die net gehaald zijn (huidige waarde exact op drempel)."""
    earned = []
    for threshold, title, description, icon in day_ms:
        if days == threshold:
            earned.append({"title": title, "description": description, "icon": icon, "category": "days"})
    for threshold, title, description, icon in week_ms:
        if weeks == threshold:
            earned.append({"title": title, "description": description, "icon": icon, "category": "weeks"})
    return earned
