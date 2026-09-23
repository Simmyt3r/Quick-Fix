from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db, limiter
from app.models import VALID_CATEGORIES
from app.uploads import cloudinary_configured, upload_avatar, upload_verification_doc
from app.validation import clean_str, valid_choice

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


@profile_bp.route("/", methods=["GET"])
@login_required
def view():
    return render_template(
        "profile/view.html",
        cloudinary_ready=cloudinary_configured(),
        categories=sorted(VALID_CATEGORIES),
    )


@profile_bp.route("/update", methods=["POST"])
@login_required
def update():
    name = clean_str(request.form.get("name"), max_length=120, required=True)
    if not name:
        flash("Name can't be empty.", "error")
        return redirect(url_for("profile.view"))

    current_user.name = name

    is_customer = request.form.get("is_customer") == "on"
    is_professional = request.form.get("is_professional") == "on"
    if is_customer or is_professional:  # never let someone uncheck both
        current_user.is_customer = is_customer
        current_user.is_professional = is_professional

    if current_user.is_professional:
        category = valid_choice(request.form.get("category"), VALID_CATEGORIES)
        if category:
            current_user.service_category = category

        profile = current_user.ensure_professional_profile()
        profile.coverage_area = clean_str(request.form.get("coverage_area"), max_length=255) or None
        profile.available = request.form.get("available") == "on"
        if not profile.available:
            # Never leave a stale position visible once a pro goes
            # offline — this is the privacy guarantee live location
            # sharing is built around (see Professional.current_lat's
            # comment in models.py).
            profile.current_lat = None
            profile.current_lng = None
            profile.location_updated_at = None
    else:
        current_user.service_category = None

    db.session.commit()
    flash("Profile updated.", "success")
    return redirect(url_for("profile.view"))


@profile_bp.route("/avatar", methods=["POST"])
@login_required
@limiter.limit("10 per hour", methods=["POST"])
def avatar():
    if not cloudinary_configured():
        flash("Photo uploads aren't configured yet.", "error")
        return redirect(url_for("profile.view"))

    file = request.files.get("avatar")
    if not file or file.filename == "":
        flash("Choose an image first.", "error")
        return redirect(url_for("profile.view"))

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        flash("Please upload a PNG, JPG, or WEBP image.", "error")
        return redirect(url_for("profile.view"))

    try:
        url = upload_avatar(file, current_user.id)
    except Exception:
        flash("Upload failed — please try a different image.", "error")
        return redirect(url_for("profile.view"))

    current_user.avatar_url = url
    db.session.commit()
    flash("Profile photo updated.", "success")
    return redirect(url_for("profile.view"))


@profile_bp.route("/verification-doc", methods=["POST"])
@login_required
@limiter.limit("10 per hour", methods=["POST"])
def verification_doc():
    if not current_user.is_professional:
        flash("Only professional accounts can upload a verification document.", "error")
        return redirect(url_for("profile.view"))
    if not cloudinary_configured():
        flash("Document uploads aren't configured yet.", "error")
        return redirect(url_for("profile.view"))

    file = request.files.get("doc")
    if not file or file.filename == "":
        flash("Choose a file first.", "error")
        return redirect(url_for("profile.view"))

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        flash("Please upload a PNG, JPG, or WEBP image of your ID or certificate.", "error")
        return redirect(url_for("profile.view"))

    try:
        public_id, doc_format = upload_verification_doc(file, current_user.id)
    except Exception:
        flash("Upload failed — please try a different image.", "error")
        return redirect(url_for("profile.view"))

    profile = current_user.ensure_professional_profile()
    profile.verification_doc_public_id = public_id
    profile.verification_doc_format = doc_format
    # A new document means whatever verification status existed before is
    # stale — an admin should look at the new upload, not carry over an
    # approval based on a since-replaced document.
    current_user.verified = False
    db.session.commit()

    flash("Document uploaded — an admin will review it shortly.", "success")
    return redirect(url_for("profile.view"))


@profile_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        current_password = request.form.get("current_password") or ""
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not current_user.password_hash:
            flash("Your account signs in with Google and has no password to change.", "error")
            return redirect(url_for("profile.settings"))
        if not current_user.check_password(current_password):
            flash("Current password is incorrect.", "error")
            return redirect(url_for("profile.settings"))
        if len(new_password) < 8:
            flash("New password must be at least 8 characters.", "error")
            return redirect(url_for("profile.settings"))
        if new_password != confirm_password:
            flash("New passwords don't match.", "error")
            return redirect(url_for("profile.settings"))

        current_user.set_password(new_password)
        db.session.commit()
        flash("Password updated.", "success")
        return redirect(url_for("profile.settings"))

    return render_template("profile/settings.html")
