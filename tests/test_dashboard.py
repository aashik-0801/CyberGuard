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
    assert b"v1.0.0" in response.data
    assert b"Workspace created" in response.data


def test_all_tool_and_profile_pages_require_authentication(client):
    for path in (
        "/tools/password-checker",
        "/tools/password-generator",
        "/profile/",
    ):
        response = client.get(path)
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]
