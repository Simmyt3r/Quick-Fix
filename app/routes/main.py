from flask import Blueprint, flash, redirect, render_template, request, url_for

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

    TODO(phase 2): persist to the `contact_submissions` table once
    Postgres/SQLAlchemy is wired up (see TODO.md). For now this just
    validates the input and logs it.
    TODO(phase 9): add CSRF protection (Flask-WTF) once forms carry a
    session-backed token.
    """
    role = request.form.get("role", "customer")
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    category = (request.form.get("category") or "").strip()
    anchor = "#pros" if role == "pro" else "#request"

    if not name or not phone:
        flash("Please add your name and phone number.", "error")
        return redirect(url_for("main.index") + anchor)

    # Placeholder until the database layer exists.
    print(f"[lead] role={role} name={name!r} phone={phone!r} category={category!r}")

    flash("Thanks — we'll be in touch shortly.", "success")
    return redirect(url_for("main.index") + anchor)
