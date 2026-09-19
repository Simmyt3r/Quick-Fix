from flask import Blueprint, abort, render_template, request

from app.extensions import db
from app.models import VALID_CATEGORIES, Review, User

pros_bp = Blueprint("pros", __name__, url_prefix="/pros")


def _rating_map(professional_ids):
    """One aggregate query for a batch of professionals, instead of a
    per-card query — avoids N+1 on the directory page."""
    if not professional_ids:
        return {}
    rows = (
        db.session.query(Review.professional_id, db.func.avg(Review.rating), db.func.count(Review.id))
        .filter(Review.professional_id.in_(professional_ids))
        .group_by(Review.professional_id)
        .all()
    )
    return {pro_id: (round(avg, 1), count) for pro_id, avg, count in rows}


@pros_bp.route("/")
def directory():
    """Public, unauthenticated directory of verified professionals."""
    category = request.args.get("category") or ""
    if category not in VALID_CATEGORIES:
        category = ""

    query = User.query.filter_by(is_professional=True, verified=True, disabled=False)
    if category:
        query = query.filter_by(service_category=category)
    pros = query.order_by(User.name.asc()).all()

    ratings = _rating_map([p.id for p in pros])

    return render_template(
        "pros/directory.html",
        pros=pros,
        ratings=ratings,
        category=category,
        categories=sorted(VALID_CATEGORIES),
    )


@pros_bp.route("/<int:pro_id>")
def profile(pro_id):
    """Public profile for a single verified professional."""
    pro = User.query.filter_by(id=pro_id, is_professional=True, verified=True, disabled=False).first()
    if pro is None:
        # 404, not a flash-and-redirect — this is a plain content page a
        # search engine or a shared link might hit directly.
        abort(404)

    rating_agg = (
        db.session.query(db.func.avg(Review.rating), db.func.count(Review.id))
        .filter(Review.professional_id == pro.id)
        .one()
    )
    avg_rating = round(rating_agg[0], 1) if rating_agg[0] is not None else None
    review_count = rating_agg[1]

    reviews = (
        Review.query.filter_by(professional_id=pro.id)
        .order_by(Review.created_at.desc())
        .limit(20)
        .all()
    )

    return render_template(
        "pros/profile.html",
        pro=pro,
        avg_rating=avg_rating,
        review_count=review_count,
        reviews=reviews,
    )
