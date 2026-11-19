from sqlalchemy import func, select

from backend.extensions import db
from backend.models import Activity


ACTIVITY_COUNTS = {
    "password_checks": "password_checker",
    "password_generations": "password_generated",
    "hash_operations": "file_hashed",
    "file_comparisons": "files_compared",
    "url_analyses": "url_analyzed",
}


def get_usage_counts(user_id: int) -> dict[str, int]:
    counts = dict(
        db.session.execute(
            select(Activity.activity_type, func.count(Activity.id))
            .where(
                Activity.user_id == user_id,
                Activity.activity_type.in_(ACTIVITY_COUNTS.values()),
            )
            .group_by(Activity.activity_type)
        ).all()
    )
    return {label: counts.get(activity_type, 0) for label, activity_type in ACTIVITY_COUNTS.items()}


def get_recent_analyses(user_id: int, limit: int = 5) -> list[Activity]:
    if limit < 1:
        raise ValueError("The recent-analysis limit must be positive.")
    return db.session.scalars(
        select(Activity)
        .where(
            Activity.user_id == user_id,
            Activity.activity_type.in_(
                ("file_hashed", "files_compared", "url_analyzed")
            ),
        )
        .order_by(Activity.timestamp.desc(), Activity.id.desc())
        .limit(limit)
    ).all()