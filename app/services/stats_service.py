"""Statistieken en trends op basis van drinkregistraties."""

from datetime import date, timedelta

from app.models import DrinkLog, Profile
from app.services.badges_service import compute_dry_streak


def weekly_limit_for_profile(profile: Profile | None) -> int:
    if profile and profile.gender and profile.gender.lower() in ("vrouw", "female", "f"):
        return 7
    return 14


def trend_start_date(since_date: date, logs: list[DrinkLog]) -> date:
    """Begin van de trendperiode: registratie, of eerder als er terugwerkende logs zijn."""
    if not logs:
        return since_date
    earliest_log = min(log.log_date for log in logs)
    return min(since_date, earliest_log)


def compute_trends(logs: list[DrinkLog], since_date: date, max_weeks: int = 26) -> dict:
    """Weektrends vanaf eerste relevante datum (registratie of oudste log) tot nu."""
    today = date.today()
    if since_date > today:
        since_date = today

    trend_start = trend_start_date(since_date, logs)
    first_week_start = trend_start - timedelta(days=trend_start.weekday())
    current_week_start = today - timedelta(days=today.weekday())
    log_by_date = {log.log_date: log.units for log in logs}

    weeks_data = []
    week_start = first_week_start

    while week_start <= current_week_start:
        week_end = week_start + timedelta(days=6)
        period_start = max(week_start, trend_start)
        period_end = min(week_end, today)

        total = 0.0
        dry_count = 0
        days_in_period = 0
        days_logged = 0
        check = period_start
        while check <= period_end:
            units = log_by_date.get(check)
            is_tracked_period = check >= since_date

            if is_tracked_period:
                days_in_period += 1
                if units is not None:
                    days_logged += 1
                    total += units
                    if units == 0:
                        dry_count += 1
            elif units is not None:
                days_in_period += 1
                days_logged += 1
                total += units
                if units == 0:
                    dry_count += 1

            check += timedelta(days=1)

        if week_start == current_week_start:
            label = f"{week_start.strftime('%d %b')} (nu)"
        else:
            label = week_start.strftime("%d %b")

        weeks_data.append({
            "label": label,
            "units": round(total, 1),
            "dry_days": dry_count,
            "days_in_period": days_in_period,
            "days_logged": days_logged,
            "is_complete": days_logged >= days_in_period if days_in_period else True,
        })
        week_start += timedelta(days=7)

    if len(weeks_data) > max_weeks:
        weeks_data = weeks_data[-max_weeks:]

    if not weeks_data:
        weeks_data.append({
            "label": f"{current_week_start.strftime('%d %b')} (nu)",
            "units": 0,
            "dry_days": 0,
            "days_in_period": max(1, (today - trend_start).days + 1),
            "days_logged": 0,
            "is_complete": False,
        })

    has_backfill = bool(logs) and min(log.log_date for log in logs) < since_date

    return {
        "labels": [w["label"] for w in weeks_data],
        "units": [w["units"] for w in weeks_data],
        "dry_days": [w["dry_days"] for w in weeks_data],
        "days_in_period": [w["days_in_period"] for w in weeks_data],
        "days_logged": [w["days_logged"] for w in weeks_data],
        "is_complete": [w["is_complete"] for w in weeks_data],
        "week_count": len(weeks_data),
        "has_backfill": has_backfill,
        "trend_start": trend_start.isoformat(),
    }


def count_logged_dry_days_this_week(logs: list[DrinkLog], since_date: date) -> int:
    """Alcoholvrije dagen deze week die expliciet met 0 glazen zijn geregistreerd."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    period_start = max(week_start, since_date)
    # Per dag kan (in tests of edge-cases) meer dan één log voorkomen.
    # Een dag telt alleen als "droog" als er wél een 0-log is en géén >0-log.
    units_by_date: dict[date, list[float]] = {}
    for log in logs:
        units_by_date.setdefault(log.log_date, []).append(log.units)

    dry_count = 0
    check = period_start
    while check <= today:
        day_units = units_by_date.get(check)
        if day_units and any(u == 0 for u in day_units) and not any(u > 0 for u in day_units):
            dry_count += 1
        check += timedelta(days=1)
    return dry_count


def compute_stats(logs: list[DrinkLog], profile: Profile | None, since_date: date) -> dict:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    week_logs = [log for log in logs if log.log_date >= week_start]
    month_logs = [log for log in logs if log.log_date >= month_start]

    week_units = sum(log.units for log in week_logs)
    month_units = sum(log.units for log in month_logs)
    limit = weekly_limit_for_profile(profile)
    period_start = max(week_start, since_date)
    week_calendar_days = max(1, (today - period_start).days + 1)
    week_days_logged = len({log.log_date for log in week_logs if log.log_date >= period_start})

    return {
        "week_units": round(week_units, 1),
        "month_units": round(month_units, 1),
        "weekly_limit": limit,
        "dry_streak": compute_dry_streak(logs, since_date),
        "days_logged": len({log.log_date for log in logs}),
        "week_days_logged": week_days_logged,
        "week_calendar_days": week_calendar_days,
        "week_incomplete": week_days_logged < week_calendar_days,
    }
