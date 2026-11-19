from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import select

from backend.extensions import db
from backend.models import Activity
from backend.services.analytics_service import (
    get_recent_analyses,
    get_usage_counts,
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/dashboard")
@login_required
def index():
    recent_activity = db.session.scalars(
        select(Activity)
        .where(Activity.user_id == current_user.id)
        .order_by(Activity.timestamp.desc())
        .limit(6)
    ).all()

    recent_analyses = get_recent_analyses(current_user.id)

    return render_template(
        "dashboard/index.html",
        recent_activity=recent_activity,
        recent_analyses=recent_analyses,
        usage_counts=get_usage_counts(current_user.id),
    )