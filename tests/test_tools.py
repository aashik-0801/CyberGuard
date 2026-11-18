import re
import string

from sqlalchemy import select

from backend.extensions import db
from backend.models import Activity
from tests.conftest import login


def test_password_checker_page_and_usage_event_do_not_accept_password(client, create_user, app):
    user = create_user()
    login(client)

    page = client.get("/tools/password-checker")
    response = client.post("/tools/password-checker/used")

    assert page.status_code == 200
    assert b"Nothing you type is sent" in page.data
    assert b"password-checker.js" in page.data
    assert response.status_code == 204
    with app.app_context():
        activity = db.session.scalar(
            select(Activity).where(
                Activity.activity_type == "password_checker",
                Activity.user_id == user.id,
            )
        )
        assert activity is not None
        assert activity.description == "Used the local password strength checker"


def test_generator_includes_each_selected_category_and_logs_no_secret(client, create_user, app):
    user = create_user()
    login(client)
    selected = {"uppercase": True, "lowercase": True, "numbers": True, "symbols": True}

    response = client.post(
        "/tools/password-generator",
        json={"length": 32, "categories": selected},
    )

    assert response.status_code == 200
    password = response.json["password"]
    assert len(password) == 32
    assert re.search(r"[A-Z]", password)
    assert re.search(r"[a-z]", password)
    assert re.search(r"[0-9]", password)
    assert any(character in "!@#$%^&*()-_=+[]{};:,.?/|~" for character in password)
    assert all(
        character in string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{};:,.?/|~"
        for character in password
    )
    with app.app_context():
        activity = db.session.scalar(
            select(Activity).where(
                Activity.activity_type == "password_generated",
                Activity.user_id == user.id,
            )
        )
        assert activity is not None
        assert activity.description == "Generated a password"
        assert password not in activity.description


def test_generator_validates_settings_and_length(client, create_user):
    create_user()
    login(client)

    no_categories = client.post(
        "/tools/password-generator",
        json={"length": 12, "categories": {"uppercase": False}},
    )
    too_short = client.post(
        "/tools/password-generator",
        json={"length": 7, "categories": {"uppercase": True, "lowercase": True, "numbers": True}},
    )
    invalid_type = client.post(
        "/tools/password-generator",
        json={"length": 12, "categories": {"uppercase": "yes"}},
    )

    assert no_categories.status_code == 400
    assert too_short.status_code == 400
    assert invalid_type.status_code == 400


def test_profile_update_and_private_account_fields(client, create_user, app):
    user = create_user()
    login(client)

    response = client.post("/profile/", data={"username": "NewName"})

    assert response.status_code == 302
    profile = client.get("/profile/")
    assert profile.status_code == 200
    assert b"NewName" in profile.data
    assert b"password_hash" not in profile.data
    assert user.password_hash.encode() not in profile.data
    with app.app_context():
        updated_user = db.session.get(type(user), user.id)
        assert updated_user.username == "NewName"
        activity = db.session.scalar(
            select(Activity).where(Activity.activity_type == "profile_updated")
        )
        assert activity is not None


def test_profile_update_rejects_existing_username(client, create_user):
    create_user(username="FirstUser")
    create_user(username="SecondUser", email="second@example.com")
    login(client, email="test@example.com")

    response = client.post("/profile/", data={"username": "SecondUser"})

    assert response.status_code == 200
    assert b"That username is already in use." in response.data
    assert b"FirstUser" in client.get("/profile/").data


def test_checker_page_is_authenticated_and_security_headers_are_present(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
