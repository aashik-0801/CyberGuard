from pathlib import Path

from sqlalchemy import select

from app import create_app
from backend.extensions import db
from backend.models import User


def test_csrf_rejects_state_changing_request_without_token(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "csrf-test-key",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'csrf.sqlite'}",
            "WTF_CSRF_ENABLED": True,
            "RATELIMIT_ENABLED": False,
        }
    )

    response = app.test_client().post(
        "/auth/register",
        data={
            "username": "TestUser",
            "email": "test@example.com",
            "password": "Unique Passphrase 42!",
            "confirm_password": "Unique Passphrase 42!",
        },
    )

    assert response.status_code == 400
    assert b"session expired" in response.data.lower()


def test_login_rate_limit_returns_safe_response(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "rate-limit-test-key",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'rate-limit.sqlite'}",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": True,
        }
    )
    client = app.test_client()

    for _ in range(10):
        response = client.post(
            "/auth/login",
            data={"email": "not-an-email", "password": "incorrect"},
            environ_base={"REMOTE_ADDR": "192.0.2.44"},
        )
        assert response.status_code == 200

    limited = client.post(
        "/auth/login",
        data={"email": "not-an-email", "password": "incorrect"},
        environ_base={"REMOTE_ADDR": "192.0.2.44"},
    )

    assert limited.status_code == 429
    assert b"Too many sign-in attempts" in limited.data


def test_database_records_survive_a_new_app_startup(tmp_path):
    database_path = Path(tmp_path) / "persistent.sqlite"
    database_url = f"sqlite:///{database_path}"
    config = {
        "TESTING": True,
        "SECRET_KEY": "persistence-test-key",
        "SQLALCHEMY_DATABASE_URI": database_url,
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": False,
    }

    first_app = create_app(config)
    with first_app.app_context():
        user = User(username="Persisted", email="persisted@example.com")
        user.set_password("A unique test passphrase")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        db.session.remove()

    second_app = create_app(config)
    with second_app.app_context():
        persisted = db.session.scalar(select(User).where(User.id == user_id))
        assert persisted is not None
        assert persisted.email == "persisted@example.com"
