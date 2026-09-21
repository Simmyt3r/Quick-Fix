from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import ContactSubmission, Incident, Payout, Review, ServiceRequest, User
from app.paystack import paystack_configured

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def home():
    context = {}

    if current_user.is_admin:
        context["service_requests"] = (
            ServiceRequest.query.order_by(ServiceRequest.created_at.desc()).limit(20).all()
        )
        context["leads"] = (
            ContactSubmission.query.order_by(ContactSubmission.created_at.desc())
            .limit(20)
            .all()
        )
        context["stats"] = {
            "total_users": User.query.count(),
            "total_customers": User.query.filter_by(is_customer=True).count(),
            "total_professionals": User.query.filter_by(is_professional=True).count(),
            "total_leads": ContactSubmission.query.count(),
            "total_requests": ServiceRequest.query.count(),
            "pending_requests": ServiceRequest.query.filter_by(status="pending").count(),
            "pending_verification": User.query.filter_by(
                is_professional=True, verified=False, disabled=False
            ).count(),
            "open_incidents": Incident.query.filter_by(status="open").count(),
            "payouts_owed_count": Payout.query.filter_by(status="owed").count(),
            "paystack_configured": paystack_configured(),
        }
        return render_template("dashboard/dashboard.html", **context)

    if current_user.is_customer:
        context["my_requests"] = (
            ServiceRequest.query.filter_by(customer_id=current_user.id)
            .order_by(ServiceRequest.created_at.desc())
            .all()
        )

    if current_user.is_professional:
        context["open_requests"] = (
            ServiceRequest.query.filter(
                ServiceRequest.status == "pending",
                ServiceRequest.category == current_user.service_category,
                db.or_(
                    ServiceRequest.requested_professional_id.is_(None),
                    ServiceRequest.requested_professional_id == current_user.id,
                ),
            )
            .order_by(ServiceRequest.created_at.desc())
            .limit(20)
            .all()
            if current_user.service_category
            else []
        )
        context["my_jobs"] = (
            ServiceRequest.query.filter(
                ServiceRequest.professional_id == current_user.id,
                ServiceRequest.status.in_(["accepted", "in_progress", "completed"]),
            )
            .order_by(ServiceRequest.created_at.desc())
            .limit(20)
            .all()
        )
        # "Leads near your trade" = anonymous landing-page leads in this pro's category.
        context["leads"] = (
            ContactSubmission.query.filter_by(
                role="customer", category=current_user.service_category
            )
            .order_by(ContactSubmission.created_at.desc())
            .limit(10)
            .all()
            if current_user.service_category
            else []
        )

        rating_agg = (
            db.session.query(db.func.avg(Review.rating), db.func.count(Review.id))
            .filter(Review.professional_id == current_user.id)
            .one()
        )
        context["avg_rating"] = round(rating_agg[0], 1) if rating_agg[0] is not None else None
        context["review_count"] = rating_agg[1]

    return render_template("dashboard/dashboard.html", **context)


@dashboard_bp.route("/jobs")
@login_required
def job_history():
    """Full, unbounded job history for a professional — the dashboard's
    "Your jobs" list is capped to the 20 most recent for a quick glance;
    this is the complete record, filterable by status."""
    if not current_user.is_professional:
        return render_template("dashboard/job_history.html", jobs=[], status_filter="all")

    status_filter = request.args.get("status") or "all"
    query = ServiceRequest.query.filter(
        ServiceRequest.professional_id == current_user.id,
        ServiceRequest.status.in_(["accepted", "in_progress", "completed", "cancelled"]),
    )
    if status_filter in ("accepted", "in_progress", "completed", "cancelled"):
        query = query.filter(ServiceRequest.status == status_filter)

    jobs = query.order_by(ServiceRequest.created_at.desc()).all()
    return render_template("dashboard/job_history.html", jobs=jobs, status_filter=status_filter)
