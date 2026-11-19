from datetime import date, timedelta

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


TOOL_ACTIVITY_TYPES = (
    "password_checker",
    "password_generated",
    "file_hashed",
    "files_compared",
    "url_analyzed",
)


def get_analytics(
    user_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict[str, object]:
    filters = [Activity.user_id == user_id]
    if date_from:
        filters.append(func.date(Activity.timestamp) >= date_from.isoformat())
    if date_to:
        filters.append(func.date(Activity.timestamp) <= date_to.isoformat())

    rows = db.session.execute(
        select(Activity.activity_type, func.count(Activity.id))
        .where(*filters)
        .group_by(Activity.activity_type)
    ).all()
    distribution = {activity_type: count for activity_type, count in rows}
    tool_counts = {
        "Password checks": distribution.get("password_checker", 0),
        "Passwords generated": distribution.get("password_generated", 0),
        "File hashes": distribution.get("file_hashed", 0),
        "File comparisons": distribution.get("files_compared", 0),
        "URL analyses": distribution.get("url_analyzed", 0),
    }

    first_date = date_from
    last_date = date_to
    if first_date is None or last_date is None:
        minimum, maximum = db.session.execute(
            select(func.min(Activity.timestamp), func.max(Activity.timestamp))
            .where(Activity.user_id == user_id)
        ).one()
        if first_date is None and minimum is not None:
            first_date = minimum.date()
        if last_date is None and maximum is not None:
            last_date = maximum.date()
    if first_date is None:
        first_date = date.today()
    if last_date is None:
        last_date = first_date
    if first_date > last_date:
        first_date, last_date = last_date, first_date

    daily_rows = db.session.execute(
        select(func.date(Activity.timestamp), Activity.activity_type, func.count(Activity.id))
        .where(*filters)
        .group_by(func.date(Activity.timestamp), Activity.activity_type)
    ).all()
    daily_map: dict[str, dict[str, int]] = {}
    for day_value, activity_type, count in daily_rows:
        daily_map.setdefault(str(day_value), {})[activity_type] = count

    labels: list[str] = []
    login_activity: list[int] = []
    failed_login_activity: list[int] = []
    logout_activity: list[int] = []
    tool_activity: list[int] = []
    daily_total: list[int] = []
    cursor = first_date
    while cursor <= last_date:
        day = cursor.isoformat()
        day_map = daily_map.get(day, {})
        labels.append(day)
        login_activity.append(day_map.get("login", 0))
        failed_login_activity.append(day_map.get("failed_login", 0))
        logout_activity.append(day_map.get("logout", 0))
        tool_activity.append(sum(day_map.get(kind, 0) for kind in TOOL_ACTIVITY_TYPES))
        daily_total.append(sum(day_map.values()))
        cursor += timedelta(days=1)

    return {
        "labels": labels,
        "login": login_activity,
        "failed_login": failed_login_activity,
        "logout": logout_activity,
        "tool_usage": tool_activity,
        "daily_total": daily_total,
        "tool_counts": tool_counts,
        "distribution": distribution,
        "total_events": sum(distribution.values()),
    }