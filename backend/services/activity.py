from backend.extensions import db
from backend.models import Activity


def record_activity(activity_type: str, description: str, user_id: int | None = None) -> None:
    db.session.add(Activity(user_id=user_id, activity_type=activity_type, description=description))
    db.session.commit()
