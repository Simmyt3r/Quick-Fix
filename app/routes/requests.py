from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db, limiter
from app.geocoding import geocode
from app.models import VALID_CATEGORIES, Payout, Review, ServiceRequest, User
from app.validation import clean_str, valid_choice, valid_int

requests_bp = Blueprint("requests", __name__, url_prefix="/requests")

VALID_URGENCY = {"today", "this_week", "flexible"}
MIN_PRICE_KOBO = 100_00  # ₦100 floor — guards against a fat-fingered ₦1 job


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
    pro_id = valid_int(request.args.get("pro_id"), min_value=1)
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

    category = valid_choice(request.form.get("category"), VALID_CATEGORIES)
    description = clean_str(request.form.get("description"), max_length=2000, required=True)
    location = clean_str(request.form.get("location"), max_length=255, required=True)
    urgency = valid_choice(request.form.get("urgency"), VALID_URGENCY, default="flexible")

    # Entered in naira, stored in kobo (Paystack's minor unit) — see the
    # comment on ServiceRequest.price in models.py for why.
    proposed_naira = valid_int(request.form.get("proposed_price"), min_value=1)
    proposed_price = proposed_naira * 100 if proposed_naira else None

    requested_professional_id = None
    pro_id = valid_int(request.form.get("requested_professional_id"), min_value=1)
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
    if not description or not location:
        flash("Please describe the job and share a location.", "error")
        return redirect(url_for("dashboard.home"))

    coords = geocode(location)
    location_lat, location_lng = coords if coords else (None, None)

    job = ServiceRequest(
        customer_id=current_user.id,
        category=category,
        description=description,
        location=location,
        location_lat=location_lat,
        location_lng=location_lng,
        urgency=urgency,
        requested_professional_id=requested_professional_id,
        proposed_price=proposed_price,
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

    # Entered in naira, stored in kobo. Defaults to the customer's
    # proposed price if the pro submits the form without changing it —
    # see requests/accept.html, which pre-fills the field with that value.
    price_naira = valid_int(request.form.get("price"), min_value=1)
    price = price_naira * 100 if price_naira else job.proposed_price

    if not price or price < MIN_PRICE_KOBO:
        flash(f"Please set a price of at least ₦{MIN_PRICE_KOBO // 100}.", "error")
        return redirect(url_for("requests.accept_form", request_id=job.id))

    job.professional_id = current_user.id
    job.price = price
    job.status = "accepted"
    db.session.commit()

    flash("Job accepted — the customer will be asked to pay before you start.", "success")
    return redirect(url_for("dashboard.home"))


@requests_bp.route("/<int:request_id>/accept", methods=["GET"])
@login_required
def accept_form(request_id):
    """Standalone page for a professional to set the price when accepting
    — a plain 'Accept' button with no price step would leave price
    unset, which the accept() route above now requires."""
    if not current_user.is_professional:
        flash("Only professional accounts can accept jobs.", "error")
        return redirect(url_for("dashboard.home"))

    job = ServiceRequest.query.get_or_404(request_id)
    if job.status != "pending":
        flash("That request has already been taken.", "error")
        return redirect(url_for("dashboard.home"))

    return render_template("requests/accept.html", job=job)


@requests_bp.route("/<int:request_id>/complete", methods=["POST"])
@login_required
def complete(request_id):
    job = ServiceRequest.query.get_or_404(request_id)

    if job.professional_id != current_user.id:
        flash("You can only complete jobs assigned to you.", "error")
        return redirect(url_for("dashboard.home"))
    if job.status != "in_progress":
        flash("This job needs to be paid for before it can be marked complete.", "error")
        return redirect(url_for("dashboard.home"))

    job.status = "completed"

    # What's owed to the professional, once a job is done. No platform
    # cut is taken yet (amount = the full price) — see the comment on
    # Payout.amount in models.py for where that would be subtracted.
    payout = Payout(service_request_id=job.id, professional_id=job.professional_id, amount=job.price)
    db.session.add(payout)
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

    rating = valid_int(request.form.get("rating"), min_value=1, max_value=5)
    comment = clean_str(request.form.get("comment"), max_length=1000) or None

    if rating is None:
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


@requests_bp.route("/<int:request_id>/track")
@login_required
def track(request_id):
    """Live map view for a customer's job — only meaningful once
    in_progress (paid, professional en route/working), since that's the
    only state Professional.current_lat/lng is being updated for THIS
    job specifically. Still viewable at other statuses, just without a
    live pin, so the URL doesn't 404 on someone who bookmarks it."""
    job = ServiceRequest.query.get_or_404(request_id)
    if job.customer_id != current_user.id:
        flash("You can only track your own requests.", "error")
        return redirect(url_for("dashboard.home"))

    return render_template("requests/track.html", job=job)
