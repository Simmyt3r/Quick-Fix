from flask import Blueprint, flash, redirect, render_template, request, url_for

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
    """Basic uptime check for the hosting platform."""
    return {"status": "ok"}, 200


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
