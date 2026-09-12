from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import ContactSubmission

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
def leads():
    """
    Capture a lead from the landing page's two call-to-action forms —
    a customer requesting a service, or a tradesperson applying to join.
    A matching professional will see customer leads under "Leads near
    your trade" on their dashboard.

    TODO(phase 9): add CSRF protection (Flask-WTF) to this public form.
    """
    role = request.form.get("role", "customer")
    if role not in ("customer", "professional"):
        role = "customer"

    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    category = (request.form.get("category") or "").strip() or None
    anchor = "#pros" if role == "professional" else "#request"

    if not name or not phone:
        flash("Please add your name and phone number.", "error")
        return redirect(url_for("main.index") + anchor)

    lead = ContactSubmission(role=role, name=name, phone=phone, category=category)
    db.session.add(lead)
    db.session.commit()

    flash("Thanks — we'll be in touch shortly.", "success")
    return redirect(url_for("main.index") + anchor)
