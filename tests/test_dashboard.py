from backend.extensions import db
from backend.models import Activity
from tests.conftest import login


def test_dashboard_requires_authentication(client):
    response = client.get("/dashboard")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_dashboard_shows_profile_and_version(client, create_user):
    create_user()
    login(client)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Welcome back, TestUser." in response.data
    assert b"CyberGuard" in response.data
    assert b"v3.0.0" in response.data
    assert b"Workspace created" in response.data


def test_dashboard_usage_counts_reflect_only_the_signed_in_users_events(client, create_user, app):
    user = create_user()
    other_user = create_user(username="OtherUser", email="other@example.com")
    with app.app_context():
        db.session.add_all(
            [
                Activity(user_id=user.id, activity_type="file_hashed", description="hash one"),
                Activity(user_id=user.id, activity_type="file_hashed", description="hash two"),
                Activity(user_id=other_user.id, activity_type="url_analyzed", description="other URL"),
            ]
        )
        db.session.commit()
    login(client)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"2</strong><span>File hashes" in response.data
    assert b"0</strong><span>URL analyses" in response.data


def test_all_tool_and_profile_pages_require_authentication(client):
    for path in (
        "/tools/password-checker",
        "/tools/password-generator",
        "/profile/",
    ):
        response = client.get(path)
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]
