"""Eigen gegevens downloaden en account verwijderen (AVG: inzage, overdraagbaarheid, vergetelheid)."""

import json
import re
from datetime import date

from flask import Response, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, logout_user

from app.blueprints.main.routes import main_bp
from app.security import login_throttle
from app.services.account_service import delete_user_account, export_drink_logs_csv, export_user_data


def _download(body: str, mimetype: str, extension: str) -> Response:
    site = re.sub(r"[^a-z0-9]+", "-", current_app.config["SITE_NAME"].lower()).strip("-") or "export"
    filename = f"{site}-gegevens-{date.today().isoformat()}.{extension}"
    response = Response(body, mimetype=mimetype)
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@main_bp.route("/account/export.json")
@login_required
def export_json():
    data = export_user_data(current_user)
    return _download(json.dumps(data, ensure_ascii=False, indent=2), "application/json", "json")


@main_bp.route("/account/export.csv")
@login_required
def export_csv():
    # BOM zodat Excel de UTF-8-tekens (×, é) goed toont.
    return _download("﻿" + export_drink_logs_csv(current_user), "text/csv; charset=utf-8", "csv")


def _reauth_key() -> str:
    return f"{request.remote_addr}|delete|{current_user.id}"


@main_bp.route("/account/verwijderen", methods=["GET", "POST"])
@login_required
def delete_account():
    is_demo = current_user.demo_expires_at is not None

    if request.method == "POST":
        key = _reauth_key()
        max_attempts = current_app.config["LOGIN_MAX_ATTEMPTS"]
        window = current_app.config["LOGIN_WINDOW_SECONDS"]

        if login_throttle.is_blocked(key, max_attempts, window):
            flash("Te veel mislukte pogingen. Probeer het over een tijdje opnieuw.", "error")
            return render_template("delete_account.html", is_demo=is_demo), 429

        if request.form.get("confirm") != "1":
            flash("Vink aan dat je begrijpt dat dit niet ongedaan kan worden.", "error")
            return render_template("delete_account.html", is_demo=is_demo), 400

        # Demo-accounts hebben een willekeurig wachtwoord dat niemand kent.
        if not is_demo and not current_user.check_password(request.form.get("password", "")):
            login_throttle.register_failure(key, window)
            flash("Onjuist wachtwoord.", "error")
            return render_template("delete_account.html", is_demo=is_demo), 400

        login_throttle.reset(key)
        user = current_user._get_current_object()
        logout_user()
        session.clear()
        delete_user_account(user)

        flash("Je account en al je gegevens zijn verwijderd.", "success")
        response = redirect(url_for("main.index"))
        # Laat de browser ook lokale kopieën (cache, service worker, opslag) van deze site wissen.
        response.headers["Clear-Site-Data"] = '"cache", "storage"'
        return response

    return render_template("delete_account.html", is_demo=is_demo)
