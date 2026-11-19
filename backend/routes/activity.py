from datetime import date

from flask import Blueprint, abort, render_template, request
from flask_login import current_user, login_required

from backend.extensions import db, limiter
from backend.services.activity import activity_query


activity_bp = Blueprint("activity", __name__, url_prefix="/activity")
ACTIVITY_CATEGORIES = (
    "login",
    "failed_login",
    "logout",
    "password_checker",
    "password_generated",
    "profile_updated",
    "file_hashed",
    "files_compared",
    "url_analyzed",
)


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        abort(400, description="Use a valid YYYY-MM-DD date.")


@activity_bp.get("/")
@login_required
@limiter.limit("60 per minute")
def index():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    if len(search) > 100 or category not in ("", *ACTIVITY_CATEGORIES):
        abort(400, description="The requested activity filters are invalid.")

    date_from = _parse_date(request.args.get("date_from", ""))
    date_to = _parse_date(request.args.get("date_to", ""))
    if date_from and date_to and date_from > date_to:
        abort(400, description="The start date must not be after the end date.")

    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        abort(400, description="Page must be a positive whole number.")
    if page < 1:
        abort(400, description="Page must be a positive whole number.")

    query = activity_query(current_user.id, search, category, date_from, date_to)
    pagination = db.paginate(query, page=page, per_page=20, error_out=False)
    return render_template(
        "activity/index.html",
        activities=pagination.items,
        pagination=pagination,
        category_options=ACTIVITY_CATEGORIES,
        filters={
            "q": search,
            "category": category,
            "date_from": date_from.isoformat() if date_from else "",
            "date_to": date_to.isoformat() if date_to else "",
        },
    )