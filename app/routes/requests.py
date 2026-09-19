from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db, limiter
from app.models import Review, ServiceRequest, User

requests_bp = Blueprint("requests", __name__, url_prefix="/requests")

VALID_CATEGORIES = {"Electrician", "Plumber", "Mechanic", "Builder", "Barber"}
VALID_URGENCY = {"today", "this_week", "flexible"}


@requests_bp.route("/new", methods=["GET"])
@login_required
def new_form():
    """Standalone full-screen request form — linked from the PWA tile grid,
    or from a professional's public profile ("Request this pro"), which
    passes pro_id to target the request at them specifically."""
    if not current_user.is_customer:
        flash("Only customer accounts can request a service.", "error")
        return redirect(url_for("dashboard.home"))

    prefill_category = request.args.get("category", "")
    requested_pro = None
    pro_id = request.args.get("pro_id")
    if pro_id:
        candidate = User.query.filter_by(id=pro_id, is_professional=True, verified=True, disabled=False).first()
        if candidate is not None:
            requested_pro = candidate
            prefill_category = candidate.service_category or prefill_category
        else:
            flash("That professional isn't available to request right now.", "error")

    return render_template(
        "requests/new.html",
        prefill_category=prefill_category,
        categories=sorted(VALID_CATEGORIES),
        requested_pro=requested_pro,
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

    requested_professional_id = None
    pro_id = request.form.get("requested_professional_id")
    if pro_id:
        candidate = User.query.filter_by(id=pro_id, is_professional=True, verified=True, disabled=False).first()
        if candidate is None:
            flash("That professional isn't available to request right now.", "error")
            return redirect(url_for("dashboard.home"))
        requested_professional_id = candidate.id
        category = candidate.service_category or category  # the job must match their trade

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
        requested_professional_id=requested_professional_id,
    )
    db.session.add(job)
    db.session.commit()

    if requested_professional_id:
        flash("Request sent to that pro — they'll accept it from their dashboard.", "success")
    else:
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
    if job.requested_professional_id and job.requested_professional_id != current_user.id:
        flash("That request was sent to a specific professional.", "error")
        return redirect(url_for("dashboard.home"))
    if not job.requested_professional_id and job.category != current_user.service_category:
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


@requests_bp.route("/<int:request_id>/review", methods=["POST"])
@login_required
@limiter.limit("20 per hour", methods=["POST"])
def review(request_id):
    job = ServiceRequest.query.get_or_404(request_id)

    if job.customer_id != current_user.id:
        flash("You can only review your own requests.", "error")
        return redirect(url_for("dashboard.home"))
    if job.status != "completed":
        flash("You can only review a job once it's marked complete.", "error")
        return redirect(url_for("dashboard.home"))
    if job.review is not None:
        flash("You've already reviewed this job.", "error")
        return redirect(url_for("dashboard.home"))

    try:
        rating = int(request.form.get("rating") or 0)
    except ValueError:
        rating = 0
    comment = (request.form.get("comment") or "").strip() or None

    if rating < 1 or rating > 5:
        flash("Please choose a rating from 1 to 5 stars.", "error")
        return redirect(url_for("dashboard.home"))

    entry = Review(
        service_request_id=job.id,
        customer_id=current_user.id,
        professional_id=job.professional_id,
        rating=rating,
        comment=comment,
    )
    db.session.add(entry)
    db.session.commit()

    flash("Thanks for the feedback!", "success")
    return redirect(url_for("dashboard.home"))
