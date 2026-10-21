import json
import logging
from urllib.parse import urlsplit

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.constants import MIN_PASSWORD_LENGTH, MIN_USERNAME_LENGTH
from app.extensions import db
from app.models import Profile, User, WebAuthnCredential
from app.security import login_throttle
from app.services.email_service import send_password_reset_email
from app.services.tokens import generate_password_reset_token, verify_password_reset_token
from app.utils import EMAIL_RE, normalize_email

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


def _safe_next_url(target: str | None) -> str | None:
    """Sta alleen relatieve paden binnen deze site toe als redirect-doel (geen open redirect)."""
    if not target:
        return None
    target = target.replace("\\", "/")
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or not target.startswith("/") or target.startswith("//"):
        return None
    return target


def _throttle_key(username: str) -> str:
    return f"{request.remote_addr}|{username}"


def _normalize_email(email: str) -> str:
    return normalize_email(email)


def _rp_config() -> dict:
    """WebAuthn RP-config. In development afgeleid van het request (localhost vs 127.0.0.1)."""
    configured_rp_id = current_app.config["WEBAUTHN_RP_ID"]
    configured_origin = current_app.config["WEBAUTHN_ORIGIN"]

    if request and current_app.debug:
        origin = request.headers.get("Origin") or f"{request.scheme}://{request.host}"
        rp_id = request.host.split(":")[0]
    else:
        origin = configured_origin
        rp_id = configured_rp_id

    return {
        "rp_id": rp_id,
        "rp_name": current_app.config["WEBAUTHN_RP_NAME"],
        "origin": origin,
    }


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        accepted_privacy = request.form.get("accept_privacy") == "1"

        if not username or len(username) < MIN_USERNAME_LENGTH:
            flash("Gebruikersnaam moet minimaal 3 tekens zijn.", "error")
        elif len(password) < MIN_PASSWORD_LENGTH:
            flash("Wachtwoord moet minimaal 8 tekens zijn.", "error")
        elif password != password2:
            flash("Wachtwoorden komen niet overeen.", "error")
        elif not accepted_privacy:
            flash("Je moet akkoord gaan met de privacyverklaring.", "error")
        elif User.query.filter_by(username=username).first():
            flash("Deze gebruikersnaam bestaat al.", "error")
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.add(Profile(user=user))
            db.session.commit()
            login_user(user)
            flash("Account aangemaakt! Vul optioneel je profiel in.", "success")
            return redirect(url_for("main.profile"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        key = _throttle_key(username)
        max_attempts = current_app.config["LOGIN_MAX_ATTEMPTS"]
        window = current_app.config["LOGIN_WINDOW_SECONDS"]

        if login_throttle.is_blocked(key, max_attempts, window):
            flash("Te veel mislukte pogingen. Probeer het over een tijdje opnieuw.", "error")
            return render_template("login.html"), 429

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_throttle.reset(key)
            session.clear()
            login_user(user, remember=bool(request.form.get("remember")))
            next_page = _safe_next_url(request.args.get("next"))
            return redirect(next_page or url_for("main.dashboard"))
        login_throttle.register_failure(key, window)
        flash("Onjuiste gebruikersnaam of wachtwoord.", "error")

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Je bent uitgelogd.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/wachtwoord-vergeten", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = _normalize_email(request.form.get("email", ""))
        if not email or not EMAIL_RE.match(email):
            flash("Vul een geldig e-mailadres in.", "error")
        else:
            profile = Profile.query.filter_by(email=email).first()
            reset_url = None
            if profile:
                token = generate_password_reset_token(profile.user)
                reset_url = url_for("auth.reset_password", token=token, _external=True)
                send_password_reset_email(email, reset_url)
            flash(
                "Als dit e-mailadres bij ons bekend is, ontvang je een resetlink.",
                "info",
            )
            if current_app.debug and reset_url:
                flash(f"Development: resetlink = {reset_url}", "info")
            return redirect(url_for("auth.login"))

    return render_template("forgot_password.html")


@auth_bp.route("/wachtwoord-reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    user = verify_password_reset_token(token)
    if not user:
        flash("De resetlink is ongeldig of verlopen.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        if len(password) < MIN_PASSWORD_LENGTH:
            flash("Wachtwoord moet minimaal 8 tekens zijn.", "error")
        elif password != password2:
            flash("Wachtwoorden komen niet overeen.", "error")
        else:
            user.set_password(password)
            db.session.commit()
            login_throttle.reset(_throttle_key(user.username))
            flash("Je wachtwoord is gewijzigd. Je kunt nu inloggen.", "success")
            return redirect(url_for("auth.login"))

    return render_template("reset_password.html", token=token)


@auth_bp.route("/passkey/register/begin", methods=["POST"])
@login_required
def passkey_register_begin():
    cfg = _rp_config()
    exclude_credentials = [
        PublicKeyCredentialDescriptor(id=cred.credential_id)
        for cred in current_user.credentials
    ]
    options = generate_registration_options(
        rp_id=cfg["rp_id"],
        rp_name=cfg["rp_name"],
        user_id=str(current_user.id).encode(),
        user_name=current_user.username,
        user_display_name=current_user.username,
        exclude_credentials=exclude_credentials or None,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    session["webauthn_challenge"] = bytes_to_base64url(options.challenge)
    return jsonify(json.loads(options_to_json(options)))


@auth_bp.route("/passkey/register/complete", methods=["POST"])
@login_required
def passkey_register_complete():
    cfg = _rp_config()
    data = request.get_json(silent=True)
    challenge = session.pop("webauthn_challenge", None)
    if not challenge:
        return jsonify({"error": "Geen actieve sessie"}), 400
    if not isinstance(data, dict):
        return jsonify({"error": "Ongeldig verzoek"}), 400

    try:
        verification = verify_registration_response(
            credential=data,
            expected_challenge=base64url_to_bytes(challenge),
            expected_rp_id=cfg["rp_id"],
            expected_origin=cfg["origin"],
        )
    except Exception:
        logger.info("Passkey-registratie mislukt", exc_info=True)
        return jsonify({"error": "Passkey kon niet worden geregistreerd"}), 400

    device_name = str(data.get("device_name") or "Passkey").strip()[:100] or "Passkey"

    cred = WebAuthnCredential(
        user_id=current_user.id,
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        device_name=device_name,
    )
    db.session.add(cred)
    db.session.commit()
    return jsonify({"success": True})


@auth_bp.route("/passkey/login/begin", methods=["POST"])
def passkey_login_begin():
    payload = request.get_json(silent=True) if request.is_json else None
    username = str((payload or {}).get("username", "")).strip().lower()
    allow_credentials = []

    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            allow_credentials = [
                PublicKeyCredentialDescriptor(id=cred.credential_id)
                for cred in user.credentials
            ]

    cfg = _rp_config()
    options = generate_authentication_options(
        rp_id=cfg["rp_id"],
        allow_credentials=allow_credentials or None,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    session["webauthn_challenge"] = bytes_to_base64url(options.challenge)
    if username:
        session["passkey_username"] = username
    return jsonify(json.loads(options_to_json(options)))


@auth_bp.route("/passkey/login/complete", methods=["POST"])
def passkey_login_complete():
    cfg = _rp_config()
    data = request.get_json(silent=True)
    challenge = session.pop("webauthn_challenge", None)
    if not challenge:
        return jsonify({"error": "Geen actieve sessie"}), 400
    if not isinstance(data, dict) or not isinstance(data.get("rawId"), str):
        return jsonify({"error": "Ongeldig verzoek"}), 400

    try:
        cred_id = base64url_to_bytes(data["rawId"])
    except Exception:
        return jsonify({"error": "Ongeldig verzoek"}), 400
    credential = WebAuthnCredential.query.filter_by(credential_id=cred_id).first()
    if not credential:
        return jsonify({"error": "Passkey niet gevonden"}), 400

    try:
        verification = verify_authentication_response(
            credential=data,
            expected_challenge=base64url_to_bytes(challenge),
            expected_rp_id=cfg["rp_id"],
            expected_origin=cfg["origin"],
            credential_public_key=credential.public_key,
            credential_current_sign_count=credential.sign_count,
        )
    except Exception:
        logger.info("Passkey-login mislukt", exc_info=True)
        return jsonify({"error": "Inloggen met passkey mislukt"}), 400

    credential.sign_count = verification.new_sign_count
    db.session.commit()
    session.clear()
    login_user(credential.user)
    return jsonify({"success": True, "redirect": url_for("main.dashboard")})


@auth_bp.route("/passkey/list")
@login_required
def passkey_list():
    creds = [
        {"id": cred.id, "name": cred.device_name, "created": cred.created_at.strftime("%d-%m-%Y")}
        for cred in current_user.credentials
    ]
    return jsonify(creds)


@auth_bp.route("/passkey/delete/<int:cred_id>", methods=["POST"])
@login_required
def passkey_delete(cred_id):
    cred = WebAuthnCredential.query.filter_by(id=cred_id, user_id=current_user.id).first()
    if cred:
        db.session.delete(cred)
        db.session.commit()
        flash("Passkey verwijderd.", "info")
    return redirect(url_for("main.profile"))
