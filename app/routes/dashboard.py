from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.models import ContactSubmission, User

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def home():
    context = {}

    if current_user.role == "professional":
        # "Leads near your trade" = customer requests filed in this pro's category.
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
        }

    return render_template("dashboard/dashboard.html", **context)
