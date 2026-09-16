from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db, limiter
from app.models import ServiceRequest

requests_bp = Blueprint("requests", __name__, url_prefix="/requests")

VALID_CATEGORIES = {"Electrician", "Plumber", "Mechanic", "Builder", "Barber"}
VALID_URGENCY = {"today", "this_week", "flexible"}


@requests_bp.route("/new", methods=["GET"])
@login_required
def new_form():
    """Standalone full-screen request form — linked from the PWA tile grid."""
    if not current_user.is_customer:
        flash("Only customer accounts can request a service.", "error")
        return redirect(url_for("dashboard.home"))
    prefill_category = request.args.get("category", "")
    return render_template(
        "requests/new.html",
        prefill_category=prefill_category,
        categories=sorted(VALID_CATEGORIES),
    )


@requests_bp.route("/new", methods=["POST"])
@login_required
@limiter.limit("20 per hour", methods=["POST"])
def new():
    if not current_user.is_customer:
        flash("Only customer accounts can request a service.", "error")
        return redirect(url_for("dashboard.home"))

    category = (request.form.get("category") or "").strip()
    description = (request.form.get("description") or "").strip()
    location = (request.form.get("location") or "").strip()
    urgency = request.form.get("urgency") or "flexible"

    if category not in VALID_CATEGORIES:
        flash("Please choose a valid category.", "error")
        return redirect(url_for("dashboard.home"))
    if urgency not in VALID_URGENCY:
        urgency = "flexible"
    if not description or not location:
        flash("Please describe the job and share a location.", "error")
        return redirect(url_for("dashboard.home"))

    job = ServiceRequest(
        customer_id=current_user.id,
        category=category,
        description=description,
        location=location,
        urgency=urgency,
    )
    db.session.add(job)
    db.session.commit()

    flash("Request sent — we'll match you with a nearby pro.", "success")
    return redirect(url_for("dashboard.home"))


@requests_bp.route("/<int:request_id>/cancel", methods=["POST"])
@login_required
def cancel(request_id):
    job = ServiceRequest.query.get_or_404(request_id)

    if job.customer_id != current_user.id:
        flash("You can only cancel your own requests.", "error")
        return redirect(url_for("dashboard.home"))
    if job.status != "pending":
        flash("Only pending requests can be cancelled.", "error")
        return redirect(url_for("dashboard.home"))

    job.status = "cancelled"
    db.session.commit()
    flash("Request cancelled.", "success")
    return redirect(url_for("dashboard.home"))


@requests_bp.route("/<int:request_id>/accept", methods=["POST"])
@login_required
def accept(request_id):
    if not current_user.is_professional:
        flash("Only professional accounts can accept jobs.", "error")
        return redirect(url_for("dashboard.home"))
    if not current_user.verified:
        flash("Your professional account needs to be verified before you can accept jobs.", "error")
        return redirect(url_for("dashboard.home"))

    job = ServiceRequest.query.get_or_404(request_id)

    if job.status != "pending":
        flash("That request has already been taken.", "error")
        return redirect(url_for("dashboard.home"))
    if job.category != current_user.service_category:
        flash("That request isn't in your trade.", "error")
        return redirect(url_for("dashboard.home"))

    job.professional_id = current_user.id
    job.status = "accepted"
    db.session.commit()

    flash("Job accepted — it now shows under Your jobs.", "success")
    return redirect(url_for("dashboard.home"))


@requests_bp.route("/<int:request_id>/complete", methods=["POST"])
@login_required
def complete(request_id):
    job = ServiceRequest.query.get_or_404(request_id)

    if job.professional_id != current_user.id:
        flash("You can only complete jobs assigned to you.", "error")
        return redirect(url_for("dashboard.home"))
    if job.status != "accepted":
        flash("Only accepted jobs can be marked complete.", "error")
        return redirect(url_for("dashboard.home"))

    job.status = "completed"
    db.session.commit()

    flash("Nice work — job marked complete.", "success")
    return redirect(url_for("dashboard.home"))
