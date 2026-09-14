from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db, limiter
from app.uploads import cloudinary_configured, upload_avatar

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")

VALID_CATEGORIES = {"Electrician", "Plumber", "Mechanic", "Builder", "Barber"}
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


@profile_bp.route("/", methods=["GET"])
@login_required
def view():
    return render_template("profile/view.html", cloudinary_ready=cloudinary_configured())


@profile_bp.route("/update", methods=["POST"])
@login_required
def update():
    name = (request.form.get("name") or "").strip()
    if not name:
        flash("Name can't be empty.", "error")
        return redirect(url_for("profile.view"))

    current_user.name = name

    if current_user.role == "professional":
        category = (request.form.get("category") or "").strip()
        if category in VALID_CATEGORIES:
            current_user.service_category = category

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
