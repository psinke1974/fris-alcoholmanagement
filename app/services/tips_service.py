"""Gepersonaliseerde tips op basis van evidence-based richtlijnen."""

from datetime import date, timedelta

from app.models import DrinkLog, Goal, Profile
from app.services.stats_service import count_logged_dry_days_this_week, weekly_limit_for_profile


def get_personalized_tips(
    user,
    profile: Profile | None,
    goals: list[Goal],
    recent_logs: list[DrinkLog],
    since_date: date,
) -> list[dict]:
    tips = []
    limit = weekly_limit_for_profile(profile)

    if not recent_logs:
        tips.append({
            "title": "Begin met bijhouden",
            "text": (
                "Onderzoek toont dat bewust registreren van alcoholgebruik op zich al helpt om minder te drinken. "
                "Log elke dag wat je drinkt — ook nul is een goede invoer."
            ),
            "category": "start",
        })
        return tips

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_logs = [log for log in recent_logs if log.log_date >= week_start]
    week_units = sum(log.units for log in week_logs)

    dry_days_this_week = count_logged_dry_days_this_week(recent_logs, since_date)
    if dry_days_this_week >= 3:
        tips.append({
            "title": "Goed bezig met alcoholvrije dagen",
            "text": (
                f"Je hebt deze week {dry_days_this_week} dag(en) met 0 glazen geregistreerd. "
                "Richtlijnen adviseren minstens 2–3 alcoholvrije dagen per week."
            ),
            "category": "positief",
        })

    if week_units > limit:
        tips.append({
            "title": "Boven de richtlijn",
            "text": (
                f"Deze week: {week_units:.1f} standaardglazen. De Nederlandse richtlijn is maximaal {limit} per week. "
                "Probeer kleinere glazen of wissel met alcoholvrije alternatieven."
            ),
            "category": "waarschuwing",
        })
    elif week_units > 0:
        tips.append({
            "title": "Binnen of onder de richtlijn",
            "text": (
                f"Je zit op {week_units:.1f} standaardglazen deze week (richtlijn: {limit}). "
                "Blijf alert: minder is altijd gezonder."
            ),
            "category": "info",
        })

    active_goal = next((goal for goal in goals if goal.active), None)
    if active_goal:
        tips.append(_tip_for_goal(active_goal, week_units))

    tips.append(_general_tip_for_day(today))

    if profile and profile.age and profile.age >= 50:
        tips.append({
            "title": "Leeftijd en alcohol",
            "text": (
                "Met de leeftijd verwerkt je lichaam alcohol trager. "
                "Minder drinken verlaagt het risico op hart- en vaatziekten, kanker en valincidenten."
            ),
            "category": "gezondheid",
        })

    return tips[:5]


def _tip_for_goal(goal: Goal, week_units: float) -> dict:
    if goal.goal_type == "weekly_units":
        remaining = max(0, goal.target_value - week_units)
        return {
            "title": "Je weekdoel",
            "text": (
                f"Doel: max {goal.target_value:.0f} glazen/week. "
                f"Nog {remaining:.1f} over deze week — plan vooruit voor het weekend."
            ),
            "category": "doel",
        }
    if goal.goal_type == "dry_days":
        return {
            "title": "Alcoholvrije dagen",
            "text": (
                f"Je streeft naar {int(goal.target_value)} alcoholvrije dagen per week. "
                "Plan ze vast in je agenda — dat vergroot de kans op succes."
            ),
            "category": "doel",
        }
    return {
        "title": "Stoppen met alcohol",
        "text": (
            "Volledig stoppen heeft de grootste gezondheidswinst. "
            "Bij ontwenningsverschijnselen: neem contact op met je huisarts. "
            "Hulp: www.alcoholinfo.nl of 0900-1995 (Trimbos)."
        ),
        "category": "doel",
    }


def _general_tip_for_day(today: date) -> dict:
    general = [
        {
            "title": "Triggers herkennen",
            "text": "Stress, vermoeidheid en sociale situaties zijn veelvoorkomende triggers. Noteer in je log wanneer je drinkt — zo zie je patronen.",
            "category": "strategie",
        },
        {
            "title": "Kleine stappen werken",
            "text": "Geleidelijk minderen is effectiever dan koud stoppen voor de meeste mensen. Verlaag met 1–2 glazen per week.",
            "category": "strategie",
        },
        {
            "title": "Alternatieven klaarzetten",
            "text": "Zet alcoholvrij bier, mocktails of bruiswater klaar vóór sociale momenten. Het vermindert de verleiding aanzienlijk.",
            "category": "strategie",
        },
        {
            "title": "Beloning werkt",
            "text": "Vier kleine successen: een alcoholvrije week, een doel gehaald. Positieve bekrachtiging versterkt gedragsverandering.",
            "category": "motivatie",
        },
        {
            "title": "Slaap en beweging",
            "text": "Voldoende slaap en beweging verminderen het verlangen naar alcohol. Probeer een wandeling in plaats van een glas wijn na werk.",
            "category": "gezondheid",
        },
    ]
    return general[today.toordinal() % len(general)]
