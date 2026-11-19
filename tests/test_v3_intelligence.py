from datetime import datetime, timezone
from unittest.mock import patch

from backend.extensions import db
from backend.models import Activity
from backend.services.device_service import collect_device_information
from backend.services.network_service import collect_network_information
from backend.services.analytics_service import get_analytics
from backend.services.recommendation_service import generate_recommendations
from tests.conftest import login


def test_device_information_has_real_fields_and_timestamp():
    with patch("backend.services.device_service.platform.system", return_value="TestOS"), \
         patch("backend.services.device_service.platform.version", return_value="1.0"), \
         patch("backend.services.device_service.platform.machine", return_value="test-arch"), \
         patch("backend.services.device_service.socket.gethostname", return_value="test-host"):
        device = collect_device_information()

    assert device["operating_system"] == "TestOS"
    assert device["os_version"] == "1.0"
    assert device["machine_architecture"] == "test-arch"
    assert device["hostname"] == "test-host"
    assert "Flask backend" in str(device["limitation"])
    assert device["collected_at"].tzinfo is not None


def test_missing_device_and_network_information_is_labelled_unavailable():
    with patch("backend.services.device_service.platform.system", return_value=""), \
         patch("backend.services.device_service.platform.version", return_value=""), \
         patch("backend.services.device_service.platform.machine", return_value=""), \
         patch("backend.services.device_service.platform.processor", return_value=""), \
         patch("backend.services.device_service.socket.gethostname", side_effect=OSError):
        device = collect_device_information()

    with patch("backend.services.network_service.socket.gethostname", side_effect=OSError), \
         patch("backend.services.network_service.socket.getaddrinfo", side_effect=OSError), \
         patch("backend.services.network_service._read_dns_configuration", return_value=[]), \
         patch("backend.services.network_service._read_default_gateway", return_value=None):
        network = collect_network_information()

    assert device["operating_system"] == "Unavailable"
    assert device["hostname"] == "Unavailable"
    assert network["hostname"] == "Unavailable"
    assert network["local_ip"] == "Unavailable"
    assert network["default_gateway"] == "Unavailable"
    assert network["dns_servers"] == []


def test_v3_pages_require_authentication(client):
    for path in (
        "/device/",
        "/network/",
        "/intelligence/analytics",
        "/intelligence/recommendations",
        "/reports/security/csv",
    ):
        response = client.get(path)
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]


def test_recommendations_use_only_signed_in_users_events(client, create_user, app):
    user = create_user()
    other = create_user(username="OtherUser", email="other@example.com")
    with app.app_context():
        db.session.add_all([
            Activity(user_id=user.id, activity_type="failed_login", description="Failed sign in"),
            Activity(user_id=user.id, activity_type="url_analyzed", description="URL indicators"),
            Activity(user_id=other.id, activity_type="file_hashed", description="Other hash"),
        ])
        db.session.commit()
        recommendations = generate_recommendations(user.id)

    titles = " ".join(item["title"] for item in recommendations)
    assert "failed sign-in" in titles
    assert "HTTP-only" in titles
    assert "provenance" not in titles


def test_analytics_and_report_are_user_scoped(client, create_user, app):
    user = create_user()
    other = create_user(username="OtherUser", email="other@example.com")
    with app.app_context():
        db.session.add_all([
            Activity(
                user_id=user.id,
                activity_type="login",
                description="Successful sign in",
                timestamp=datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
            ),
            Activity(
                user_id=user.id,
                activity_type="file_hashed",
                description="Generated a SHA-256 file hash",
                timestamp=datetime(2026, 11, 18, 13, 0, tzinfo=timezone.utc),
            ),
            Activity(
                user_id=other.id,
                activity_type="failed_login",
                description="Other account secret",
            ),
        ])
        db.session.commit()
        analytics = get_analytics(
            user.id,
            datetime(2026, 11, 18, tzinfo=timezone.utc).date(),
            datetime(2026, 11, 18, tzinfo=timezone.utc).date(),
        )

    assert analytics["total_events"] == 2
    assert analytics["tool_counts"]["File hashes"] == 1

    login(client)
    analytics_response = client.get(
        "/intelligence/analytics.json?date_from=2026-11-18&date_to=2026-11-18"
    )
    csv_response = client.get("/reports/security/csv")
    html_response = client.get("/reports/security/html")

    assert analytics_response.status_code == 200
    assert analytics_response.get_json()["total_events"] == 2
    assert csv_response.status_code == 200
    assert csv_response.mimetype == "text/csv"
    assert b"3.0.0" in csv_response.data
    assert b"not a complete security audit" in csv_response.data
    assert html_response.status_code == 200
    assert html_response.mimetype == "text/html"
