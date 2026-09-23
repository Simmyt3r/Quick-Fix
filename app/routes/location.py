from datetime import datetime

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from app.extensions import db, limiter
from app.models import ServiceRequest
from app.realtime import authenticate_channel, broadcast_professional_location, pusher_configured
from app.validation import valid_int

location_bp = Blueprint("location", __name__, url_prefix="/location")

# A sane bound on real-world coordinates — guards against a garbled or
# spoofed payload rather than trusting whatever the browser sends outright.
MIN_LAT, MAX_LAT = -90, 90
MIN_LNG, MAX_LNG = -180, 180


def _valid_coord(value, lo, hi):
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f < lo or f > hi:
        return None
    return f


@location_bp.route("/update", methods=["POST"])
@login_required
@limiter.limit("120 per hour", methods=["POST"])  # roughly one update every 30s, generous headroom
def update():
    """
    Called by a professional's browser (see static/js/location-share.js)
    while they're marked available, and separately while working an
    in_progress job. Always updates Professional.current_lat/lng — that's
    what distance-sorted matching reads. Additionally broadcasts over
    Pusher if the update is tied to a specific in_progress job the
    caller is the assigned professional on, so the customer's live map
    updates.
    """
    if not current_user.is_professional:
        return jsonify({"error": "not a professional account"}), 403

    lat = _valid_coord(request.form.get("lat"), MIN_LAT, MAX_LAT)
    lng = _valid_coord(request.form.get("lng"), MIN_LNG, MAX_LNG)
    if lat is None or lng is None:
        return jsonify({"error": "invalid coordinates"}), 400

    profile = current_user.ensure_professional_profile()
    profile.current_lat = lat
    profile.current_lng = lng
    profile.location_updated_at = datetime.utcnow()
    db.session.commit()

    job_id = valid_int(request.form.get("job_id"), min_value=1)
    if job_id:
        job = ServiceRequest.query.filter_by(
            id=job_id, professional_id=current_user.id, status="in_progress"
        ).first()
        if job:
            broadcast_professional_location(job.id, lat, lng)

    return jsonify({"status": "ok"})


@location_bp.route("/pusher-auth", methods=["POST"])
@login_required
def pusher_auth():
    """
    Pusher's JS SDK calls this before letting the browser subscribe to a
    private channel — we decide here whether this specific user is
    allowed onto this specific channel. Only the job's own customer may
    subscribe to its tracking channel; nobody else, including other
    customers or the professional themselves (they're the one sending
    updates, not receiving them).
    """
    if not pusher_configured():
        abort(404)

    channel_name = request.form.get("channel_name", "")
    socket_id = request.form.get("socket_id", "")

    if not channel_name.startswith("private-job-"):
        abort(403)

    try:
        job_id = int(channel_name.removeprefix("private-job-"))
    except ValueError:
        abort(403)

    job = ServiceRequest.query.filter_by(id=job_id, customer_id=current_user.id).first()
    if job is None:
        abort(403)

    auth = authenticate_channel(channel_name, socket_id)
    return jsonify(auth)
