"""Detectie van gaten in drinkregistraties en inhaalmodus."""

from datetime import date, timedelta

from app.constants import GAP_MIN_DAYS
from app.models import DrinkLog


def detect_gaps(
    logs: list[DrinkLog],
    since_date: date,
    dismissed_until: date | None = None,
    min_gap_days: int = GAP_MIN_DAYS,
) -> list[dict]:
    """Zoek opeenvolgende dagen zonder registratie (vanaf eerste relevante log tot gisteren)."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    logged_dates = {log.log_date for log in logs}
    if not logged_dates:
        return []

    relevant_dates = {d for d in logged_dates if d >= since_date}
    period_start = min(relevant_dates) if relevant_dates else min(logged_dates)

    if period_start > yesterday:
        return []

    gaps: list[dict] = []
    gap_start: date | None = None
    check = period_start

    while check <= yesterday:
        if check not in logged_dates:
            if gap_start is None:
                gap_start = check
        elif gap_start is not None:
            gap_end = check - timedelta(days=1)
            _append_gap(gaps, gap_start, gap_end, min_gap_days)
            gap_start = None
        check += timedelta(days=1)

    if gap_start is not None:
        _append_gap(gaps, gap_start, yesterday, min_gap_days)

    if dismissed_until:
        gaps = [g for g in gaps if g["end"] > dismissed_until]

    return gaps


def get_active_gap(
    logs: list[DrinkLog],
    since_date: date,
    dismissed_until: date | None = None,
) -> dict | None:
    """Oudste nog niet opgeloste gat — voor inhaalmodus."""
    gaps = detect_gaps(logs, since_date, dismissed_until)
    if not gaps:
        return None
    gap = gaps[0]
    return {
        **gap,
        "days_list": _date_range(gap["start"], gap["end"]),
        "label_start": gap["start"].strftime("%d %b"),
        "label_end": gap["end"].strftime("%d %b %Y"),
    }


def _append_gap(gaps: list[dict], start: date, end: date, min_gap_days: int) -> None:
    days = (end - start).days + 1
    if days >= min_gap_days:
        gaps.append({"start": start, "end": end, "days": days})


def _date_range(start: date, end: date) -> list[date]:
    result = []
    check = start
    while check <= end:
        result.append(check)
        check += timedelta(days=1)
    return result
