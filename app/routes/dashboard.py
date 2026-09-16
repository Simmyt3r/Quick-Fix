from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.models import ContactSubmission, Incident, ServiceRequest, User

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
            ServiceRequest.query.filter_by(
                status="pending", category=current_user.service_category
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
                ServiceRequest.status.in_(["accepted", "completed"]),
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

    return render_template("dashboard/dashboard.html", **context)
