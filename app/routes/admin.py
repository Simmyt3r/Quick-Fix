from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import AdminAction, Incident, PlatformSetting, Payout, ServiceRequest, User
from app.uploads import verification_doc_url
from app.validation import clean_str, valid_choice, valid_int

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

INCIDENT_CATEGORIES = {"no_show", "dispute", "complaint", "other"}
INCIDENT_CATEGORY_LABELS = {
    "no_show": "No-show",
    "dispute": "Payment dispute",
    "complaint": "Complaint",
    "other": "Other",
}


def admin_required(view):
    """Like @login_required, but 404s (not 403) for non-admins — same reasoning
    as returning 404 for someone else's resource: don't reveal that an /admin
    area exists to a logged-in customer or professional poking at URLs."""

    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(404)
        return view(*args, **kwargs)

    return wrapped


def log_action(action, target_user=None, target_incident=None, detail=None):
    entry = AdminAction(
        admin_id=current_user.id,
        action=action,
        target_user_id=target_user.id if target_user else None,
        target_incident_id=target_incident.id if target_incident else None,
        detail=detail,
    )
    db.session.add(entry)


# ─────────────────────── Verification queue ───────────────────────

@admin_bp.route("/verification")
@admin_required
def verification_queue():
    pending = (
        User.query.filter_by(is_professional=True, verified=False, disabled=False)
        .order_by(User.created_at.asc())
        .all()
    )

    doc_urls = {}
    for u in pending:
        profile = u.professional_profile
        if profile and profile.verification_doc_public_id:
            try:
                doc_urls[u.id] = verification_doc_url(
                    profile.verification_doc_public_id, profile.verification_doc_format
                )
            except Exception:
                # Cloudinary not configured, or a transient API error — the
                # queue should still render without a working link rather
                # than 500 the whole page over one bad document.
                pass

    return render_template("admin/verification.html", pending=pending, doc_urls=doc_urls)


@admin_bp.route("/verification/<int:user_id>/approve", methods=["POST"])
@admin_required
def approve_professional(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_professional:
        flash("That account isn't a professional account.", "error")
        return redirect(url_for("admin.verification_queue"))

    user.verified = True
    log_action("verify_professional", target_user=user, detail=f"trade: {user.service_category or 'unset'}")
    db.session.commit()

    flash(f"{user.name} is now verified.", "success")
    return redirect(url_for("admin.verification_queue"))


@admin_bp.route("/verification/<int:user_id>/reject", methods=["POST"])
@admin_required
def reject_professional(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_professional:
        flash("That account isn't a professional account.", "error")
        return redirect(url_for("admin.verification_queue"))

    reason = clean_str(request.form.get("reason"), max_length=255)
    user.verified = False  # explicit — guards against re-approving a previously-verified pro by mistake
    log_action("reject_professional", target_user=user, detail=reason or None)
    db.session.commit()

    flash(f"{user.name}'s verification was rejected.", "success")
    return redirect(url_for("admin.verification_queue"))


# ─────────────────────── User management ───────────────────────

@admin_bp.route("/users")
@admin_required
def users():
    q = clean_str(request.args.get("q"), max_length=120)
    role_filter = valid_choice(request.args.get("role"), {"customer", "professional", "admin"}, default="")
    status_filter = valid_choice(request.args.get("status"), {"disabled", "active", "unverified_pro"}, default="")

    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(User.name.ilike(like), User.email.ilike(like)))
    if role_filter == "customer":
        query = query.filter_by(is_customer=True)
    elif role_filter == "professional":
        query = query.filter_by(is_professional=True)
    elif role_filter == "admin":
        query = query.filter_by(role="admin")
    if status_filter == "disabled":
        query = query.filter_by(disabled=True)
    elif status_filter == "active":
        query = query.filter_by(disabled=False)
    elif status_filter == "unverified_pro":
        query = query.filter_by(is_professional=True, verified=False)

    results = query.order_by(User.created_at.desc()).limit(200).all()
    return render_template(
        "admin/users.html",
        results=results,
        q=q,
        role_filter=role_filter,
        status_filter=status_filter,
    )


@admin_bp.route("/users/<int:user_id>/disable", methods=["POST"])
@admin_required
def disable_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You can't disable your own account.", "error")
        return redirect(url_for("admin.users"))
    if user.is_admin:
        flash("Admin accounts can't be disabled from here.", "error")
        return redirect(url_for("admin.users"))

    reason = clean_str(request.form.get("reason"), max_length=255)
    user.disabled = True
    log_action("disable_user", target_user=user, detail=reason or None)
    db.session.commit()

    flash(f"{user.name}'s account is disabled.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/enable", methods=["POST"])
@admin_required
def enable_user(user_id):
    user = User.query.get_or_404(user_id)

    user.disabled = False
    log_action("enable_user", target_user=user)
    db.session.commit()

    flash(f"{user.name}'s account is re-enabled.", "success")
    return redirect(url_for("admin.users"))


# ─────────────────────── Incidents ───────────────────────

@admin_bp.route("/incidents")
@admin_required
def incidents():
    status_filter = valid_choice(request.args.get("status"), {"open", "resolved", "all"}, default="open")
    query = Incident.query
    if status_filter in ("open", "resolved"):
        query = query.filter_by(status=status_filter)
    entries = query.order_by(Incident.created_at.desc()).limit(100).all()
    return render_template(
        "admin/incidents.html",
        entries=entries,
        status_filter=status_filter,
        category_labels=INCIDENT_CATEGORY_LABELS,
    )


@admin_bp.route("/incidents/new", methods=["GET", "POST"])
@admin_required
def new_incident():
    if request.method == "POST":
        category = valid_choice(request.form.get("category"), INCIDENT_CATEGORIES, default="other")
        note = clean_str(request.form.get("note"), max_length=2000, required=True)
        subject_user_id = valid_int(request.form.get("subject_user_id"), min_value=1)
        service_request_id = valid_int(request.form.get("service_request_id"), min_value=1)

        if not note:
            flash("Please describe what happened.", "error")
            return redirect(url_for("admin.new_incident"))

        subject_user = User.query.get(subject_user_id) if subject_user_id else None
        service_request = ServiceRequest.query.get(service_request_id) if service_request_id else None

        incident = Incident(
            reported_by_id=current_user.id,
            subject_user_id=subject_user.id if subject_user else None,
            service_request_id=service_request.id if service_request else None,
            category=category,
            note=note,
        )
        db.session.add(incident)
        db.session.flush()  # assign incident.id before logging it
        log_action("log_incident", target_user=subject_user, target_incident=incident, detail=category)
        db.session.commit()

        flash("Incident logged.", "success")
        return redirect(url_for("admin.incidents"))

    prefill_user_id = request.args.get("user_id", "")
    prefill_request_id = request.args.get("request_id", "")
    return render_template(
        "admin/incident_new.html",
        prefill_user_id=prefill_user_id,
        prefill_request_id=prefill_request_id,
        categories=sorted(INCIDENT_CATEGORIES),
        category_labels=INCIDENT_CATEGORY_LABELS,
    )


@admin_bp.route("/incidents/<int:incident_id>/resolve", methods=["POST"])
@admin_required
def resolve_incident(incident_id):
    from datetime import datetime

    incident = Incident.query.get_or_404(incident_id)
    incident.status = "resolved"
    incident.resolved_at = datetime.utcnow()
    log_action("resolve_incident", target_user=incident.subject_user, target_incident=incident)
    db.session.commit()

    flash("Incident marked resolved.", "success")
    return redirect(url_for("admin.incidents"))


# ─────────────────────── Audit log ───────────────────────

@admin_bp.route("/activity")
@admin_required
def activity():
    entries = AdminAction.query.order_by(AdminAction.created_at.desc()).limit(150).all()
    return render_template("admin/activity.html", entries=entries)


# ─────────────────────── Platform settings (Paystack) ───────────────────────

@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    row = PlatformSetting.query.get(1)
    if row is None:
        row = PlatformSetting(id=1)
        db.session.add(row)
        db.session.commit()

    if request.method == "POST":
        public_key = clean_str(request.form.get("paystack_public_key"), max_length=255)
        secret_key = clean_str(request.form.get("paystack_secret_key"), max_length=255)

        row.paystack_public_key = public_key or None
        # Only overwrite the stored secret if a new one was actually
        # typed — the form never echoes the real secret back (see the
        # template), so a blank submit means "leave it as-is", not
        # "clear it".
        if secret_key:
            row.paystack_secret_key = secret_key
        row.updated_by_id = current_user.id

        log_action("update_platform_settings", detail="Paystack keys updated")
        db.session.commit()

        flash("Payment settings saved.", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html", row=row)


# ─────────────────────── Payouts ───────────────────────

@admin_bp.route("/payouts")
@admin_required
def payouts():
    status_filter = valid_choice(request.args.get("status"), {"owed", "paid", "all"}, default="owed")
    query = Payout.query
    if status_filter in ("owed", "paid"):
        query = query.filter_by(status=status_filter)
    entries = query.order_by(Payout.created_at.desc()).limit(200).all()
    total_owed = (
        db.session.query(db.func.coalesce(db.func.sum(Payout.amount), 0))
        .filter(Payout.status == "owed")
        .scalar()
    )
    return render_template(
        "admin/payouts.html", entries=entries, status_filter=status_filter, total_owed=total_owed
    )


@admin_bp.route("/payouts/<int:payout_id>/mark-paid", methods=["POST"])
@admin_required
def mark_payout_paid(payout_id):
    from datetime import datetime

    payout = Payout.query.get_or_404(payout_id)
    if payout.status == "paid":
        flash("That payout is already marked paid.", "error")
        return redirect(url_for("admin.payouts"))

    payout.status = "paid"
    payout.paid_at = datetime.utcnow()
    payout.paid_by_id = current_user.id
    log_action(
        "mark_payout_paid",
        target_user=payout.professional,
        detail=f"₦{payout.amount / 100:,.2f} for job #{payout.service_request_id}",
    )
    db.session.commit()

    flash("Payout marked as sent.", "success")
    return redirect(url_for("admin.payouts"))
