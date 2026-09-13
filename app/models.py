from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    # Nullable: Google-only accounts have no password to check.
    password_hash = db.Column(db.String(255), nullable=True)
    # Google's "sub" claim — stable even if the person changes their Google email.
    google_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    role = db.Column(db.String(20), nullable=False, default="customer")  # customer | professional | admin

    # Professional-only fields, kept on the same table for now to stay
    # "basic" — see TODO.md for the fuller `professionals` table (coverage
    # area, rating, total_jobs, etc.) that README's data model describes.
    service_category = db.Column(db.String(50), nullable=True)
    verified = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False  # Google-only account — there's no password to match.
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class ContactSubmission(db.Model):
    """Leads captured from the landing page's two call-to-action forms."""

    __tablename__ = "contact_submissions"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # customer | professional
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ServiceRequest(db.Model):
    """A customer's request for a tradesperson — the core booking loop."""

    __tablename__ = "service_requests"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    urgency = db.Column(db.String(20), nullable=False, default="flexible")  # today | this_week | flexible
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending | accepted | completed | cancelled

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("User", foreign_keys=[customer_id], backref="requests_made")
    professional = db.relationship("User", foreign_keys=[professional_id], backref="jobs_taken")

    def __repr__(self):
        return f"<ServiceRequest {self.id} {self.category} {self.status}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
