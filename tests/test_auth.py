from sqlalchemy import select

from backend.extensions import db
from backend.models import Activity, User
from tests.conftest import login, register


def test_registration_hashes_password_and_normalizes_email(client, app):
    response = register(client, email="TEST@EXAMPLE.COM")

    assert response.status_code == 302
    with app.app_context():
        user = db.session.scalar(select(User).where(User.email == "test@example.com"))
        assert user is not None
        assert user.password_hash != "Unique Passphrase 42!"
        assert user.check_password("Unique Passphrase 42!")


def test_registration_rejects_duplicate_email_case_insensitively(client, app):
    assert register(client).status_code == 302
    response = register(client, username="AnotherUser", email="TEST@example.com")

    assert response.status_code == 409
    with app.app_context():
        assert db.session.scalar(select(db.func.count()).select_from(User)) == 1


def test_registration_rejects_duplicate_username_case_insensitively(client, app):
    assert register(client).status_code == 302
    response = register(client, username="testuser", email="another@example.com")

    assert response.status_code == 409
    with app.app_context():
        assert db.session.scalar(select(db.func.count()).select_from(User)) == 1


def test_registration_validates_password_confirmation(client):
    response = client.post(
        "/auth/register",
        data={
            "username": "TestUser",
            "email": "test@example.com",
            "password": "Unique Passphrase 42!",
            "confirm_password": "different password",
        },
    )

    assert response.status_code == 200
    assert b"Passwords must match." in response.data


def test_login_records_successful_activity(client, create_user, app):
    user = create_user()

    response = login(client)

    assert response.status_code == 302
    assert b"Welcome back, TestUser." in client.get("/dashboard").data
    with app.app_context():
        activity = db.session.scalar(
            select(Activity).where(Activity.activity_type == "login", Activity.user_id == user.id)
        )
        assert activity is not None
        assert activity.description == "Successful sign in"


def test_invalid_login_uses_generic_message_and_records_failure(client, create_user, app):
    user = create_user()

    response = login(client, password="not-the-password")

    assert response.status_code == 200
    assert b"The email or password was not recognized." in response.data
    with app.app_context():
        activity = db.session.scalar(
            select(Activity).where(Activity.activity_type == "failed_login")
        )
        assert activity is not None
        assert activity.user_id == user.id
        assert "not-the-password" not in activity.description


def test_unknown_email_failure_does_not_store_email_or_password(client, app):
    response = login(client, email="unknown@example.com", password="sensitive-value")

    assert response.status_code == 200
    with app.app_context():
        activity = db.session.scalar(select(Activity).where(Activity.activity_type == "failed_login"))
        assert activity is not None
        assert activity.user_id is None
        assert "unknown@example.com" not in activity.description
        assert "sensitive-value" not in activity.description


def test_logout_records_activity_and_clears_session(client, create_user, app):
    user = create_user()
    assert login(client).status_code == 302

    response = client.post("/auth/logout")

    assert response.status_code == 302
    assert b"Sign in" in client.get("/dashboard", follow_redirects=True).data
    with app.app_context():
        activity = db.session.scalar(
            select(Activity).where(Activity.activity_type == "logout", Activity.user_id == user.id)
        )
        assert activity is not None
