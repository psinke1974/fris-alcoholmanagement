from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.constants import DRINK_OPTIONS, EDUCATION_LEVELS, GENDERS, MAX_UNITS_PER_DAY
from app.extensions import db
from app.models import DrinkLog, Goal, Profile
from app.services import compute_badges, compute_stats, compute_trends, get_active_gap, get_cessation_guidance, get_personalized_tips
from app.services.drinks_service import (
    calculate_units_from_items,
    format_drink_summary,
    log_entry_for_client,
    parse_drink_items,
    serialize_drink_items,
)
from app.utils import EMAIL_RE, normalize_email

main_bp = Blueprint("main", __name__)

# Toegestane doeltypes met maximale doelwaarde
GOAL_LIMITS = {"weekly_units": 100, "dry_days": 7, "abstain": 0}


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("landing.html")


@main_bp.route("/privacy")
def privacy():
    return render_template("privacy.html")


@main_bp.route("/over")
def about():
    return render_template("over.html")


@main_bp.route("/partners")
def partners():
    """One-pager voor GGD's, gemeenten en gezondheidsinstituten."""
    return render_template("partners.html", wide_container=True)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    logs = (
        DrinkLog.query.filter_by(user_id=current_user.id)
        .order_by(DrinkLog.log_date.desc())
        .limit(365)
        .all()
    )
    goals = Goal.query.filter_by(user_id=current_user.id, active=True).all()
    profile = current_user.profile
    since_date = current_user.created_at.date()
    active_goal = next((g for g in goals if g.active), None)
    chart_weekly_goal = None
    chart_dry_days_goal = None
    if active_goal:
        if active_goal.goal_type == "weekly_units":
            chart_weekly_goal = float(active_goal.target_value)
        elif active_goal.goal_type == "abstain":
            chart_weekly_goal = 0.0
        elif active_goal.goal_type == "dry_days":
            chart_dry_days_goal = float(active_goal.target_value)

    return render_template(
        "dashboard.html",
        stats=compute_stats(logs, profile, since_date),
        trends=compute_trends(logs, since_date),
        tips=get_personalized_tips(current_user, profile, goals, logs, since_date),
        phase_guidance=get_cessation_guidance(goals, logs, since_date),
        badges=compute_badges(logs, since_date),
        recent=logs[:7],
        goals=goals,
        profile=profile,
        chart_weekly_goal=chart_weekly_goal,
        chart_dry_days_goal=chart_dry_days_goal,
        active_gap=get_active_gap(logs, since_date, current_user.gap_prompt_dismissed_until),
    )


@main_bp.route("/log", methods=["GET", "POST"])
@login_required
def log_drink():
    if request.method == "POST":
        log_date_str = request.form.get("log_date", "")
        drink_items = parse_drink_items(request.form.get("drink_items", ""))
        notes = request.form.get("notes", "").strip()[:255]

        try:
            log_date = date.fromisoformat(log_date_str)
        except (ValueError, TypeError):
            flash("Ongeldige datum.", "error")
            return redirect(url_for("main.log_drink"))

        if drink_items:
            units = calculate_units_from_items(drink_items)
            drink_type = format_drink_summary(drink_items)
        else:
            units = 0.0
            drink_type = None

        if units < 0 or units > MAX_UNITS_PER_DAY:
            flash(f"Totaal aantal standaardglazen is te hoog (max {MAX_UNITS_PER_DAY}).", "error")
            return redirect(url_for("main.log_drink"))

        existing = DrinkLog.query.filter_by(user_id=current_user.id, log_date=log_date).first()

        if existing:
            existing.units = units
            existing.drink_type = drink_type or None
            existing.drink_items = serialize_drink_items(drink_items)
            existing.notes = notes or None
            flash("Registratie bijgewerkt.", "success")
        else:
            db.session.add(DrinkLog(
                user_id=current_user.id,
                log_date=log_date,
                units=units,
                drink_type=drink_type or None,
                drink_items=serialize_drink_items(drink_items),
                notes=notes or None,
            ))
            flash("Registratie opgeslagen.", "success")

        db.session.commit()
        return redirect(url_for("main.dashboard"))

    cutoff = date.today() - timedelta(days=365)
    logs = (
        DrinkLog.query.filter(
            DrinkLog.user_id == current_user.id,
            DrinkLog.log_date >= cutoff,
        )
        .all()
    )
    existing_logs = {
        log.log_date.isoformat(): log_entry_for_client(log)
        for log in logs
    }

    return render_template(
        "log.html",
        drink_options=DRINK_OPTIONS,
        today=date.today().isoformat(),
        selected_date=request.args.get("date", date.today().isoformat()),
        existing_logs=existing_logs,
    )


def _user_logs(user_id: int) -> list[DrinkLog]:
    return (
        DrinkLog.query.filter_by(user_id=user_id)
        .order_by(DrinkLog.log_date.desc())
        .limit(365)
        .all()
    )


def _parse_gap_dates() -> tuple[date, date] | None:
    start_str = request.form.get("gap_start", "")
    end_str = request.form.get("gap_end", "")
    try:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
    except (ValueError, TypeError):
        return None
    if start > end:
        return None
    return start, end


def _validate_gap_action(start: date, end: date, active_gap: dict) -> bool:
    yesterday = date.today() - timedelta(days=1)
    if end > yesterday or start > end:
        return False
    return start == active_gap["start"] and end == active_gap["end"]


@main_bp.route("/catch-up", methods=["GET", "POST"])
@login_required
def catch_up():
    since_date = current_user.created_at.date()
    logs = _user_logs(current_user.id)
    active_gap = get_active_gap(logs, since_date, current_user.gap_prompt_dismissed_until)

    if request.method == "POST":
        if not active_gap:
            return redirect(url_for("main.dashboard"))

        gap_range = _parse_gap_dates()
        if not gap_range:
            flash("Ongeldige periode.", "error")
            return redirect(url_for("main.catch_up"))

        gap_start, gap_end = gap_range
        if (gap_start, gap_end) != (active_gap["start"], active_gap["end"]):
            flash("Deze periode is niet meer actueel. Probeer opnieuw.", "error")
            return redirect(url_for("main.catch_up"))

        if not _validate_gap_action(gap_start, gap_end, active_gap):
            flash("Ongeldige datums voor deze periode.", "error")
            return redirect(url_for("main.catch_up"))

        action = request.form.get("action", "")

        if action == "dry_all":
            _fill_gap_days(current_user.id, gap_start, gap_end, units=0.0)
            db.session.commit()
            flash(f"{active_gap['days']} dag(en) geregistreerd als niet gedronken.", "success")
            return redirect(url_for("main.catch_up"))

        if action == "skip":
            current_user.gap_prompt_dismissed_until = gap_end
            db.session.commit()
            flash("Periode overgeslagen — onbekende dagen tellen niet mee in je statistieken.", "info")
            return redirect(url_for("main.dashboard"))

        if action == "dry_day":
            log_date_str = request.form.get("log_date", "")
            try:
                log_date = date.fromisoformat(log_date_str)
            except (ValueError, TypeError):
                flash("Ongeldige datum.", "error")
                return redirect(url_for("main.catch_up"))

            if log_date < gap_start or log_date > gap_end:
                flash("Datum valt buiten de geselecteerde periode.", "error")
                return redirect(url_for("main.catch_up"))

            existing = DrinkLog.query.filter_by(user_id=current_user.id, log_date=log_date).first()
            if not existing:
                db.session.add(DrinkLog(
                    user_id=current_user.id,
                    log_date=log_date,
                    units=0.0,
                ))
                db.session.commit()
                flash(f"{log_date.strftime('%d-%m-%Y')}: niet gedronken geregistreerd.", "success")
            return redirect(url_for("main.catch_up"))

        flash("Onbekende actie.", "error")
        return redirect(url_for("main.catch_up"))

    if not active_gap:
        return redirect(url_for("main.dashboard"))

    return render_template("catch_up.html", gap=active_gap)


def _fill_gap_days(user_id: int, start: date, end: date, units: float) -> int:
    filled = 0
    check = start
    while check <= end:
        existing = DrinkLog.query.filter_by(user_id=user_id, log_date=check).first()
        if not existing:
            db.session.add(DrinkLog(user_id=user_id, log_date=check, units=units))
            filled += 1
        check += timedelta(days=1)
    return filled


@main_bp.route("/log/delete/<int:log_id>", methods=["POST"])
@login_required
def delete_log(log_id):
    entry = DrinkLog.query.filter_by(id=log_id, user_id=current_user.id).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
        flash("Registratie verwijderd.", "info")
    return redirect(url_for("main.log_drink"))


@main_bp.route("/goals", methods=["GET", "POST"])
@login_required
def goals():
    if request.method == "POST":
        goal_type = request.form.get("goal_type")
        target_str = request.form.get("target_value", "")

        try:
            target = float(target_str.replace(",", "."))
        except (ValueError, OverflowError):
            flash("Ongeldig doel.", "error")
            return redirect(url_for("main.goals"))

        if goal_type not in GOAL_LIMITS:
            flash("Onbekend type doel.", "error")
            return redirect(url_for("main.goals"))

        if goal_type == "abstain":
            target = 0
        elif not (0 <= target <= GOAL_LIMITS[goal_type]):
            flash(f"Doelwaarde moet tussen 0 en {GOAL_LIMITS[goal_type]} liggen.", "error")
            return redirect(url_for("main.goals"))

        Goal.query.filter_by(user_id=current_user.id, active=True).update({"active": False})
        db.session.add(Goal(
            user_id=current_user.id,
            goal_type=goal_type,
            target_value=target,
            start_date=date.today(),
            active=True,
        ))
        db.session.commit()
        flash("Nieuw doel ingesteld!", "success")
        return redirect(url_for("main.goals"))

    return render_template(
        "goals.html",
        active_goals=Goal.query.filter_by(user_id=current_user.id, active=True).all(),
        history=Goal.query.filter_by(user_id=current_user.id, active=False)
        .order_by(Goal.created_at.desc())
        .limit(5)
        .all(),
    )


@main_bp.route("/goals/deactivate/<int:goal_id>", methods=["POST"])
@login_required
def deactivate_goal(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if goal:
        goal.active = False
        db.session.commit()
        flash("Doel gedeactiveerd.", "info")
    return redirect(url_for("main.goals"))


def _option_values(options) -> set:
    return {opt[0] if isinstance(opt, (tuple, list)) else opt for opt in options}


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    prof = current_user.profile
    if not prof:
        prof = Profile(user_id=current_user.id)
        db.session.add(prof)
        db.session.commit()

    if request.method == "POST":
        age_str = request.form.get("age", "").strip()
        email_raw = request.form.get("email", "").strip()
        gender = request.form.get("gender") or None
        education = request.form.get("education") or None
        prof.gender = gender if gender in _option_values(GENDERS) else None
        prof.education = education if education in _option_values(EDUCATION_LEVELS) else None
        prof.country = request.form.get("country", "").strip()[:100] or None

        if email_raw:
            email = normalize_email(email_raw)
            if not EMAIL_RE.match(email):
                flash("Vul een geldig e-mailadres in.", "error")
                return redirect(url_for("main.profile"))
            existing = Profile.query.filter(Profile.email == email, Profile.id != prof.id).first()
            if existing:
                flash("Dit e-mailadres is al in gebruik.", "error")
                return redirect(url_for("main.profile"))
            prof.email = email
        else:
            prof.email = None

        if age_str:
            try:
                age = int(age_str)
                if 13 <= age <= 120:
                    prof.age = age
                else:
                    flash("Leeftijd moet tussen 13 en 120 zijn.", "error")
                    return redirect(url_for("main.profile"))
            except ValueError:
                flash("Ongeldige leeftijd.", "error")
                return redirect(url_for("main.profile"))
        else:
            prof.age = None

        db.session.commit()
        flash("Profiel opgeslagen.", "success")
        return redirect(url_for("main.profile"))

    return render_template(
        "profile.html",
        profile=prof,
        genders=GENDERS,
        education_levels=EDUCATION_LEVELS,
        credentials=current_user.credentials,
    )


@main_bp.route("/dagboek", methods=["GET", "POST"])
@login_required
def journal():
    from app.services.journal_service import (
        delete_entry,
        get_entries_for_user,
        get_entry,
        is_empty_body,
        save_entry,
    )

    if request.method == "POST":
        entry_id_str = request.form.get("entry_id", "").strip()
        entry_date_str = request.form.get("entry_date", "")
        title = request.form.get("title", "").strip()
        body_html = request.form.get("body_html", "")

        try:
            entry_date = date.fromisoformat(entry_date_str)
        except (ValueError, TypeError):
            flash("Ongeldige datum.", "error")
            return redirect(url_for("main.journal"))

        if is_empty_body(body_html):
            flash("Schrijf iets in je dagboek voordat je opslaat.", "error")
            edit_id = int(entry_id_str) if entry_id_str.isdigit() else None
            if edit_id:
                return redirect(url_for("main.journal", edit=edit_id))
            return redirect(url_for("main.journal"))

        entry_id = int(entry_id_str) if entry_id_str.isdigit() else None
        save_entry(current_user.id, entry_date, body_html, title=title, entry_id=entry_id)
        flash("Dagboekentry opgeslagen.", "success")
        return redirect(url_for("main.journal"))

    edit_id = request.args.get("edit", type=int)
    editing = get_entry(current_user.id, edit_id) if edit_id else None

    return render_template(
        "journal.html",
        entries=get_entries_for_user(current_user.id),
        editing=editing,
        today=date.today().isoformat(),
    )


@main_bp.route("/dagboek/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_journal_entry(entry_id):
    from app.services.journal_service import delete_entry

    if delete_entry(current_user.id, entry_id):
        flash("Dagboekentry verwijderd.", "info")
    else:
        flash("Entry niet gevonden.", "error")
    return redirect(url_for("main.journal"))
