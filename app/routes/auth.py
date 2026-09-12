from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db, limiter
from app.models import User

auth_bp = Blueprint("auth", __name__)

VALID_ROLES = {"customer", "professional"}


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
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        role = request.form.get("role") or "customer"
        category = (request.form.get("category") or "").strip() or None

        if role not in VALID_ROLES:
            role = "customer"

        if not name or not email or len(password) < 8:
            flash("Please fill in your name, email, and an 8+ character password.", "error")
            return render_template("auth/register.html"), 400

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
            return render_template("auth/register.html"), 400

        user = User(
            name=name,
            email=email,
            role=role,
            service_category=category if role == "professional" else None,
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
