from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager

# Single source of truth for service categories — several routes and
# templates need this set (registration, the request form, the public
# directory, profile settings), and it used to be copy-pasted in three
# different files with no guarantee they'd stay in sync.
VALID_CATEGORIES = {"Electrician", "Plumber", "Mechanic", "Builder", "Barber"}


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    # Nullable: Google-only accounts have no password to check.
    password_hash = db.Column(db.String(255), nullable=True)
    # Google's "sub" claim — stable even if the person changes their Google email.
    google_id = db.Column(db.String(255), unique=True, nullable=True, index=True)

    # A user can be a customer, a professional, or both at once — hence two
    # independent flags rather than a single role string. `role` is kept only
    # to flag admins, who are a separate, exclusive account type.
    is_customer = db.Column(db.Boolean, nullable=False, default=True)
    is_professional = db.Column(db.Boolean, nullable=False, default=False)
    role = db.Column(db.String(20), nullable=False, default="customer")  # customer | admin (legacy values may still say "professional" pre-migration)

    # Professional-only fields, kept on the same table for now to stay
    # "basic" — see TODO.md for the fuller `professionals` table (coverage
    # area, rating, total_jobs, etc.) that README's data model describes.
    service_category = db.Column(db.String(50), nullable=True)
    verified = db.Column(db.Boolean, nullable=False, default=False)

    # Admin-managed account status. A disabled user can't log in (password
    # or Google) and their open service requests/leads stop surfacing to
    # professionals — see auth.py and dashboard.py.
    disabled = db.Column(db.Boolean, nullable=False, default=False)

    avatar_url = db.Column(db.String(500), nullable=True)  # Cloudinary secure_url

    # Password reset. token is a random URL-safe string, not a signed JWT —
    # storing it lets us make it genuinely single-use (cleared on success)
    # and revocable, rather than relying purely on a signature's expiry.
    # Nullable: most users have no reset in flight most of the time.
    reset_token = db.Column(db.String(100), nullable=True, unique=True, index=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False  # Google-only account — there's no password to match.
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        types = "+".join(t for t, flag in (("customer", self.is_customer), ("professional", self.is_professional)) if flag) or self.role
        return f"<User {self.email} ({types})>"

    @property
    def is_admin(self):
        return self.role == "admin"

    def ensure_professional_profile(self):
        """Get this user's Professional row, creating one with defaults if
        it doesn't exist yet — covers accounts that became professional
        after the professionals table was added (existing rows were
        backfilled in migration 74671caae830, but a customer who later
        checks "professional" in Settings won't have one until now)."""
        if self.professional_profile is None:
            self.professional_profile = Professional(user_id=self.id)
            db.session.add(self.professional_profile)
        return self.professional_profile


class Professional(db.Model):
    """Extra profile fields for a professional account, one-to-one with
    User. service_category and verified stay on User itself — they're
    load-bearing in enough places (login-time checks, the accept-job
    guard, the admin verification queue) that moving them isn't worth
    the risk right now. This table is for genuinely new fields that
    don't exist anywhere yet."""

    __tablename__ = "professionals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    coverage_area = db.Column(db.String(255), nullable=True)  # free-text for now, e.g. "Wuse, Garki, Asokoro"
    available = db.Column(db.Boolean, nullable=False, default=True)  # toggled by the pro; False = "not taking jobs right now"

    # Verification document — a photo of an ID/certificate, uploaded to
    # Cloudinary as a private asset (never a public URL, unlike avatars).
    # doc_format is needed alongside the public_id to build a signed URL
    # later (see uploads.verification_doc_url).
    verification_doc_public_id = db.Column(db.String(255), nullable=True)
    verification_doc_format = db.Column(db.String(10), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("professional_profile", uselist=False))

    def __repr__(self):
        return f"<Professional user_id={self.user_id} available={self.available}>"


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
    # Set when a customer books via a professional's public profile ("Request
    # this pro") rather than the open category-matching flow. When set, only
    # this professional can accept the job — see requests.py:accept.
    requested_professional_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    urgency = db.Column(db.String(20), nullable=False, default="flexible")  # today | this_week | flexible
    # pending -> accepted (price set, awaiting payment) -> in_progress (paid,
    # work underway) -> completed. cancelled can happen from pending or accepted.
    status = db.Column(db.String(20), nullable=False, default="pending")

    proposed_price = db.Column(db.Integer, nullable=True)  # customer's optional budget, in kobo (NGN minor unit)
    price = db.Column(db.Integer, nullable=True)  # the actual agreed price, in kobo — set when the pro accepts

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("User", foreign_keys=[customer_id], backref="requests_made")
    professional = db.relationship("User", foreign_keys=[professional_id], backref="jobs_taken")
    requested_professional = db.relationship("User", foreign_keys=[requested_professional_id])

    def __repr__(self):
        return f"<ServiceRequest {self.id} {self.category} {self.status}>"


class PlatformSetting(db.Model):
    """Admin-configurable platform settings — currently just the Paystack
    API keys. Values are stored encrypted (app/crypto.py) since this is
    the one place in the app holding live payment-provider credentials.
    A single-row table by convention (id=1) rather than free-form
    key/value pairs, since there's exactly one thing to configure today;
    revisit if a second setting shows up."""

    __tablename__ = "platform_settings"

    id = db.Column(db.Integer, primary_key=True)
    paystack_public_key = db.Column(db.String(255), nullable=True)  # not secret — safe in plaintext, used client-side
    paystack_secret_key_encrypted = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    updated_by = db.relationship("User")

    @property
    def paystack_secret_key(self):
        from app.crypto import decrypt_value

        return decrypt_value(self.paystack_secret_key_encrypted)

    @paystack_secret_key.setter
    def paystack_secret_key(self, value):
        from app.crypto import encrypt_value

        self.paystack_secret_key_encrypted = encrypt_value(value)

    @property
    def is_configured(self):
        return bool(self.paystack_public_key and self.paystack_secret_key)

    def __repr__(self):
        return f"<PlatformSetting configured={self.is_configured}>"


class Payment(db.Model):
    """One row per payment attempt on a service request. A job can have
    more than one Payment row if a checkout attempt fails or expires and
    the customer tries again — only one should ever reach status='paid'
    per service_request_id, enforced in the route, not the schema (a DB
    constraint would block legitimate retries after a failed attempt)."""

    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey("service_requests.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    paystack_reference = db.Column(db.String(100), nullable=False, unique=True)
    amount = db.Column(db.Integer, nullable=False)  # kobo
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending | paid | failed

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)

    service_request = db.relationship("ServiceRequest", backref="payments")
    customer = db.relationship("User")

    def __repr__(self):
        return f"<Payment {self.paystack_reference} {self.status}>"


class Payout(db.Model):
    """What's owed (and, once handled, paid) to a professional for a
    completed and paid job. Manually marked by an admin for now — no
    automated bank transfer yet, that needs the professional to have a
    Paystack transfer recipient on file, which is its own sub-flow."""

    __tablename__ = "payouts"

    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey("service_requests.id"), nullable=False, unique=True)
    professional_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    amount = db.Column(db.Integer, nullable=False)  # kobo — the job's price, minus the platform's cut once one exists
    status = db.Column(db.String(20), nullable=False, default="owed")  # owed | paid
    paid_at = db.Column(db.DateTime, nullable=True)
    paid_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # which admin marked it paid

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    service_request = db.relationship("ServiceRequest", backref=db.backref("payout", uselist=False))
    professional = db.relationship("User", foreign_keys=[professional_id])
    paid_by = db.relationship("User", foreign_keys=[paid_by_id])

    def __repr__(self):
        return f"<Payout job={self.service_request_id} {self.status}>"


class Review(db.Model):
    """A customer's rating of a completed job. One review per service
    request — reviewing is customer-to-professional only for now; if
    two-way reviews are ever added, add a `direction` column rather than
    reusing this table's one-row-per-request assumption."""

    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(
        db.Integer, db.ForeignKey("service_requests.id"), nullable=False, unique=True
    )
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    service_request = db.relationship("ServiceRequest", backref=db.backref("review", uselist=False))
    customer = db.relationship("User", foreign_keys=[customer_id])
    professional = db.relationship("User", foreign_keys=[professional_id], backref="reviews_received")

    def __repr__(self):
        return f"<Review {self.id} {self.rating}★ for pro {self.professional_id}>"


class Incident(db.Model):
    """An admin-facing report attached to a user and/or a service request —
    e.g. a no-show, a payment dispute, or a complaint. Not raised by
    customers/professionals themselves yet (no public report form); admins
    log these directly for now."""

    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    reported_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey("service_requests.id"), nullable=True)

    category = db.Column(db.String(30), nullable=False)  # no_show | dispute | complaint | other
    note = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="open")  # open | resolved

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    reported_by = db.relationship("User", foreign_keys=[reported_by_id])
    subject_user = db.relationship("User", foreign_keys=[subject_user_id])
    service_request = db.relationship("ServiceRequest")

    def __repr__(self):
        return f"<Incident {self.id} {self.category} {self.status}>"


class AdminAction(db.Model):
    """Audit trail of admin actions — who did what, to whom, when. Written
    automatically by admin routes (verify, disable, resolve incident, etc.),
    never edited or deleted through the app."""

    __tablename__ = "admin_actions"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # e.g. "verify_professional", "disable_user"
    target_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    target_incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=True)
    detail = db.Column(db.String(255), nullable=True)  # short human-readable context, no PII beyond what's already on-screen

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship("User", foreign_keys=[admin_id])
    target_user = db.relationship("User", foreign_keys=[target_user_id])
    target_incident = db.relationship("Incident")

    def __repr__(self):
        return f"<AdminAction {self.action} by {self.admin_id}>"


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user is not None and user.disabled:
        return None  # forces Flask-Login to treat the session as logged out
    return user
