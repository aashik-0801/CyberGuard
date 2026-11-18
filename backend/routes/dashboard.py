from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import select

from backend.extensions import db
from backend.models import Activity

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
    return render_template("dashboard/index.html", recent_activity=recent_activity)
