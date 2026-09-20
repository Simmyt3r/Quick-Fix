from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app.extensions import db, limiter
from app.models import VALID_CATEGORIES, ContactSubmission
from app.validation import clean_str, valid_choice

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Marketing landing page."""
    return render_template("index.html")


@main_bp.route("/healthz")
def healthz():
    """
    Uptime/health check for the hosting platform. Actually touches the
    database rather than returning a static 200 — a health check that
    can't detect the DB being unreachable isn't telling you anything
    useful, and that's exactly the failure mode this project already
    hit once (migrations silently not applied in production).
    """
    try:
        db.session.execute(db.text("SELECT 1"))
        return {"status": "ok"}, 200
    except Exception as exc:
        current_app.logger.error("Health check DB failure: %s", exc)
        return {"status": "error", "detail": "database unreachable"}, 503


@main_bp.route("/leads", methods=["POST"])
@limiter.limit("10 per hour")
def leads():
    """
    Capture a lead from the landing page's two call-to-action forms —
    a customer requesting a service, or a tradesperson applying to join.
    A matching professional will see customer leads under "Leads near
    your trade" on their dashboard.
    """
    role = valid_choice(request.form.get("role"), {"customer", "professional"}, default="customer")
    name = clean_str(request.form.get("name"), max_length=120, required=True)
    phone = clean_str(request.form.get("phone"), max_length=30, required=True)
    category = valid_choice(request.form.get("category"), VALID_CATEGORIES)
    anchor = "#pros" if role == "professional" else "#request"

    if not name or not phone:
        flash("Please add your name and phone number.", "error")
        return redirect(url_for("main.index") + anchor)

    lead = ContactSubmission(role=role, name=name, phone=phone, category=category)
    db.session.add(lead)
    db.session.commit()

    flash("Thanks — we'll be in touch shortly.", "success")
    return redirect(url_for("main.index") + anchor)
