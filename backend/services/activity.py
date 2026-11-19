from datetime import date

from sqlalchemy import func, or_, select

from backend.extensions import db
from backend.models import Activity


def record_activity(activity_type: str, description: str, user_id: int | None = None) -> None:
    db.session.add(Activity(user_id=user_id, activity_type=activity_type, description=description))
    db.session.commit()


def activity_query(
    user_id: int,
    search: str = "",
    category: str = "",
    date_from: date | None = None,
    date_to: date | None = None,
):
    query = select(Activity).where(Activity.user_id == user_id)
    if search:
        query = query.where(
            or_(
                Activity.description.contains(search, autoescape=True),
                Activity.activity_type.contains(search, autoescape=True),
            )
        )
    if category:
        query = query.where(Activity.activity_type == category)
    if date_from:
        query = query.where(func.date(Activity.timestamp) >= date_from.isoformat())
    if date_to:
        query = query.where(func.date(Activity.timestamp) <= date_to.isoformat())
    return query.order_by(Activity.timestamp.desc(), Activity.id.desc())
