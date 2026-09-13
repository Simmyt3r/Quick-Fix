from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.models import ContactSubmission, ServiceRequest, User

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def home():
    context = {}

    if current_user.role == "customer":
        context["my_requests"] = (
            ServiceRequest.query.filter_by(customer_id=current_user.id)
            .order_by(ServiceRequest.created_at.desc())
            .all()
        )

    elif current_user.role == "professional":
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

    elif current_user.role == "admin":
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
            "total_customers": User.query.filter_by(role="customer").count(),
            "total_professionals": User.query.filter_by(role="professional").count(),
            "total_leads": ContactSubmission.query.count(),
            "total_requests": ServiceRequest.query.count(),
            "pending_requests": ServiceRequest.query.filter_by(status="pending").count(),
        }

    return render_template("dashboard/dashboard.html", **context)
