from datetime import datetime, timedelta
from secrets import token_urlsafe
from urllib.parse import urlparse

import requests
from authlib.integrations.base_client.errors import OAuthError
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db, limiter, oauth
from app.mail import send_email
from app.models import VALID_CATEGORIES, User
from app.validation import clean_str, valid_choice, valid_email

auth_bp = Blueprint("auth", __name__)

RESET_TOKEN_TTL = timedelta(hours=1)

def _safe_next(target):
    """Only follow `next` if it's a relative, same-site path — never an open redirect."""
    if not target:
        return None
    parsed = urlparse(target)
    if parsed.netloc or parsed.scheme:
        return None
    return target


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        name = clean_str(request.form.get("name"), max_length=120, required=True)
        email = valid_email(request.form.get("email"))
        password = request.form.get("password") or ""
        # Checkboxes: both may be checked, but at least one is required.
        is_customer = request.form.get("is_customer") == "on"
        is_professional = request.form.get("is_professional") == "on"
        category = valid_choice(request.form.get("category"), VALID_CATEGORIES)

        if not is_customer and not is_professional:
            is_customer = True  # sensible default rather than an accountless user

        if not name or not email or len(password) < 8:
            flash("Please fill in your name, a valid email, and an 8+ character password.", "error")
            return render_template("auth/register.html"), 400

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
            return render_template("auth/register.html"), 400

        user = User(
            name=name,
            email=email,
            is_customer=is_customer,
            is_professional=is_professional,
            service_category=category if is_professional else None,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Welcome to QuickFix Nearby!", "success")
        return redirect(url_for("dashboard.home"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash("Incorrect email or password.", "error")
            return render_template("auth/login.html"), 401
        if user.disabled:
            flash("This account has been disabled. Contact support if you think that's a mistake.", "error")
            return render_template("auth/login.html"), 403

        login_user(user)
        flash(f"Welcome back, {user.name.split(' ')[0]}.", "success")
        return redirect(_safe_next(request.args.get("next")) or url_for("dashboard.home"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        user = User.query.filter_by(email=email).first()

        # Always show the same message whether or not the account exists, or
        # whether it even has a password — telling someone "no account with
        # that email" or "that account uses Google" from this form is an
        # account-enumeration leak. The right message for either case goes
        # in the email itself, sent only to the real inbox.
        if user is not None and not user.disabled:
            if user.password_hash is None:
                send_email(
                    user.email,
                    "Password reset — QuickFix Nearby",
                    f"Hi {user.name.split(' ')[0]},\n\n"
                    "Someone (hopefully you) requested a password reset for this "
                    "email on QuickFix Nearby. This account signs in with Google, "
                    "though, so there's no password to reset — just use the "
                    '"Continue with Google" button on the login page.\n\n'
                    "If this wasn't you, no action is needed.\n\n"
                    "— QuickFix Nearby",
                )
            else:
                user.reset_token = token_urlsafe(32)
                user.reset_token_expires = datetime.utcnow() + RESET_TOKEN_TTL
                db.session.commit()

                reset_url = url_for("auth.reset_password", token=user.reset_token, _external=True)
                sent = send_email(
                    user.email,
                    "Password reset — QuickFix Nearby",
                    f"Hi {user.name.split(' ')[0]},\n\n"
                    "Someone (hopefully you) requested a password reset for this "
                    "email on QuickFix Nearby. This link works for 1 hour:\n\n"
                    f"{reset_url}\n\n"
                    "If this wasn't you, no action is needed — your password "
                    "stays the same.\n\n"
                    "— QuickFix Nearby",
                )
                if not sent:
                    # SMTP isn't configured (e.g. local dev) — log the link so
                    # the flow is still testable without real email delivery.
                    current_app.logger.info("Password reset link for %s: %s", user.email, reset_url)

        flash(
            "If an account exists for that email, we've sent a link to reset the password.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    user = User.query.filter_by(reset_token=token).first()
    token_valid = (
        user is not None
        and not user.disabled
        and user.reset_token_expires is not None
        and user.reset_token_expires > datetime.utcnow()
    )

    if not token_valid:
        flash("That reset link is invalid or has expired. Request a new one below.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("auth/reset_password.html", token=token), 400
        if password != confirm:
            flash("Those passwords don't match.", "error")
            return render_template("auth/reset_password.html", token=token), 400

        user.set_password(password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()

        flash("Your password has been reset. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)


@auth_bp.route("/login/google")
@limiter.limit("20 per hour")
def google_login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if not current_app.config["GOOGLE_OAUTH_ENABLED"]:
        flash("Google sign-in isn't set up on this server yet.", "error")
        return redirect(url_for("auth.login"))

    # Same idea as the password login's `next` support — remember where to
    # send the person once Google hands them back to us.
    session["post_google_login_next"] = _safe_next(request.args.get("next"))
    redirect_uri = url_for("auth.google_callback", _external=True)
    try:
        return oauth.google.authorize_redirect(redirect_uri)
    except (OAuthError, requests.exceptions.RequestException):
        # Google's discovery endpoint didn't respond — don't 500, just bounce back.
        flash("Couldn't reach Google right now — please try again in a moment.", "error")
        return redirect(url_for("auth.login"))


@auth_bp.route("/google-callback")
def google_callback():
    if not current_app.config["GOOGLE_OAUTH_ENABLED"]:
        flash("Google sign-in isn't set up on this server yet.", "error")
        return redirect(url_for("auth.login"))

    try:
        token = oauth.google.authorize_access_token()
    except (OAuthError, requests.exceptions.RequestException):
        # Covers a denied consent screen, an expired/mismatched state (e.g.
        # the login was started a long time ago), Google rejecting the code
        # exchange, or Google simply not responding — none of these 500.
        flash("Google sign-in didn't go through — please try again.", "error")
        return redirect(url_for("auth.login"))

    profile = token.get("userinfo") or oauth.google.userinfo(token=token)

    google_id = profile.get("sub")
    email = (profile.get("email") or "").strip().lower()
    email_verified = profile.get("email_verified", False)
    name = profile.get("name") or (email.split("@")[0] if email else "there")

    if not google_id or not email or not email_verified:
        flash(
            "That Google account's email isn't verified, so we can't use it to sign in. "
            "Try a different Google account, or register with a password instead.",
            "error",
        )
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(google_id=google_id).first()
    is_new_account = False

    if user is None:
        # No account linked to this Google ID yet. Google has already
        # confirmed the email above, so it's safe to attach this login to a
        # matching password account rather than creating a duplicate.
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(name=name, email=email, is_customer=True, is_professional=False)
            db.session.add(user)
            is_new_account = True
        user.google_id = google_id
        db.session.commit()

    if user.disabled:
        flash("This account has been disabled. Contact support if you think that's a mistake.", "error")
        return redirect(url_for("auth.login"))

    login_user(user)
    first_name = user.name.split(" ")[0] if user.name else "there"
    flash("Welcome to QuickFix Nearby!" if is_new_account else f"Welcome back, {first_name}.", "success")
    next_target = session.pop("post_google_login_next", None)
    return redirect(next_target or url_for("dashboard.home"))
