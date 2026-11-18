import pytest

from app import create_app
from backend.extensions import db
from backend.models import User


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key-not-for-production",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        }
    )
    with application.app_context():
        db.drop_all()
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def create_user(app):
    def create(username="TestUser", email="test@example.com", password="Unique Passphrase 42!"):
        user = User(username=username, email=email.lower())
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    return create


def register(client, username="TestUser", email="test@example.com", password="Unique Passphrase 42!"):
    return client.post(
        "/auth/register",
        data={
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )


def login(client, email="test@example.com", password="Unique Passphrase 42!"):
    return client.post("/auth/login", data={"email": email, "password": password})
