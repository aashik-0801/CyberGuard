from datetime import datetime, timezone

from backend.extensions import db
from backend.models import Activity
from tests.conftest import login


def test_activity_search_category_date_and_authorization(client, create_user, app):
    first = create_user(username="FirstUser")
    second = create_user(username="OtherUser", email="other@example.com")
    with app.app_context():
        db.session.add_all(
            [
                Activity(
                    user_id=first.id,
                    activity_type="file_hashed",
                    description="Generated a SHA-256 file hash",
                    timestamp=datetime(2026, 11, 18, tzinfo=timezone.utc),
                ),
                Activity(
                    user_id=second.id,
                    activity_type="url_analyzed",
                    description="Other account secret event",
                    timestamp=datetime(2026, 11, 18, tzinfo=timezone.utc),
                ),
            ]
        )
        db.session.commit()
    login(client, email="test@example.com")

    filtered = client.get(
        "/activity/?category=file_hashed&date_from=2026-11-18&date_to=2026-11-18&q=SHA-256"
    )
    search = client.get("/activity/?q=Other+account")

    assert filtered.status_code == 200
    assert b"Generated a SHA-256 file hash" in filtered.data
    assert b"Other account secret event" not in filtered.data
    assert search.status_code == 200
    assert b"Other account secret event" not in search.data


def test_activity_pagination_and_csv_export_are_user_scoped(client, create_user, app):
    user = create_user()
    other_user = create_user(username="OtherUser", email="other@example.com")
    with app.app_context():
        db.session.add_all(
            [
                Activity(
                    user_id=user.id,
                    activity_type="file_hashed",
                    description=f"File hash event {index}",
                )
                for index in range(25)
            ]
        )
        db.session.add(
            Activity(
                user_id=other_user.id,
                activity_type="url_analyzed",
                description="Private other-account event",
            )
        )
        db.session.commit()
    login(client)

    page_two = client.get("/activity/?page=2")
    export = client.get("/reports/activity/csv")

    assert page_two.status_code == 200
    assert b"Page 2 of 2" in page_two.data
    assert export.status_code == 200
    assert export.mimetype == "text/csv"
    assert b"File hash event" in export.data
    assert b"Private other-account event" not in export.data