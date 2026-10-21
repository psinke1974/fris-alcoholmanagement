import logging
import smtplib
from email.message import EmailMessage

from flask import current_app, render_template

logger = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    return bool(current_app.config.get("MAIL_SERVER"))


def send_email(to: str, subject: str, text_body: str, html_body: str | None = None) -> bool:
    """Verstuur een e-mail. In development zonder SMTP wordt de mail gelogd."""
    if not to:
        return False

    if not _smtp_configured():
        logger.info("E-mail (geen SMTP geconfigureerd):\nAan: %s\nOnderwerp: %s\n\n%s", to, subject, text_body)
        return True

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    msg["To"] = to
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    use_tls = current_app.config.get("MAIL_USE_TLS", True)
    port = current_app.config.get("MAIL_PORT", 587)
    server_addr = current_app.config["MAIL_SERVER"]
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")

    with smtplib.SMTP(server_addr, port) as smtp:
        if use_tls:
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(msg)

    return True


def send_password_reset_email(to: str, reset_url: str) -> bool:
    site_name = current_app.config["SITE_NAME"]
    subject = f"Wachtwoord resetten — {site_name}"
    text_body = render_template("email/password_reset.txt", reset_url=reset_url, site_name=site_name)
    html_body = render_template("email/password_reset.html", reset_url=reset_url, site_name=site_name)
    return send_email(to, subject, text_body, html_body)
