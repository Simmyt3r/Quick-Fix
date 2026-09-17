import os
import smtplib
from email.message import EmailMessage


def smtp_configured():
    """True once SMTP credentials are present."""
    return bool(os.environ.get("SMTP_USERNAME") and os.environ.get("SMTP_PASSWORD"))


def init_mail(app):
    """Just logs a warning at startup if SMTP isn't configured — there's no
    SDK to initialize here, unlike Cloudinary, so this mainly exists to keep
    the same "one warning at boot" pattern the other integrations use."""
    if not smtp_configured():
        app.logger.warning(
            "SMTP env vars not set — password reset emails will be logged instead of sent "
            "until SMTP_USERNAME/SMTP_PASSWORD are configured."
        )


def send_email(to_address, subject, body_text):
    """
    Send a plain-text email via Gmail SMTP (smtp.gmail.com:587, STARTTLS).
    Requires a Gmail App Password in SMTP_PASSWORD, not the account's normal
    password — Google blocks plain password auth for third-party SMTP.

    Returns True if sent, False if SMTP isn't configured (caller decides how
    to degrade — see auth.py, which logs the email instead of failing the
    request). Raises smtplib exceptions on an actual send failure so the
    caller can decide whether to surface an error.
    """
    if not smtp_configured():
        return False

    username = os.environ["SMTP_USERNAME"]
    password = os.environ["SMTP_PASSWORD"]
    from_address = os.environ.get("MAIL_FROM") or username

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address
    msg.set_content(body_text)

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(msg)

    return True
