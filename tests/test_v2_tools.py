import csv
import hashlib
import io
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from backend.extensions import db
from backend.models import Activity
from backend.services.file_comparison_service import compare_streams
from backend.services.hash_service import FileTooLargeError, hash_stream
from backend.services.report_service import build_activity_report
from backend.services.url_analysis_service import analyze_url
from tests.conftest import login


def test_hash_stream_handles_empty_and_chunked_files():
    empty_hash, empty_size = hash_stream(io.BytesIO(b""))
    content = b"abc" * 500_000
    large_hash, large_size = hash_stream(io.BytesIO(content))

    assert empty_hash == hashlib.sha256(b"").hexdigest()
    assert empty_size == 0
    assert large_hash == hashlib.sha256(content).hexdigest()
    assert large_size == len(content)


def test_hash_stream_rejects_files_over_limit():
    with pytest.raises(FileTooLargeError):
        hash_stream(io.BytesIO(b"0123456789"), max_bytes=9)


def test_file_comparison_reports_matching_and_different_content():
    same = compare_streams(io.BytesIO(b"same"), io.BytesIO(b"same"))
    different = compare_streams(io.BytesIO(b"left"), io.BytesIO(b"right"))

    assert same["match"] is True
    assert same["original_hash"] == same["comparison_hash"]
    assert different["match"] is False
    assert different["original_hash"] != different["comparison_hash"]


@pytest.mark.parametrize("value", ["", "not a URL", "ftp://example.com", "https:///missing-host"])
def test_url_analyzer_rejects_invalid_urls(value):
    with pytest.raises(ValueError):
        analyze_url(value)


def test_url_analyzer_rejects_whitespace_in_url_host():
    with pytest.raises(ValueError):
        analyze_url("https://example .com")


def test_url_analyzer_identifies_http_https_and_suspicious_indicators():
    https_result = analyze_url("https://example.com")
    http_result = analyze_url("http://example.com")
    suspicious = analyze_url("http://xn--example-9d0b.com/login")

    assert https_result["uses_https"] is True
    assert http_result["uses_https"] is False
    assert any("HTTP" in indicator for indicator in http_result["indicators"])
    assert suspicious["has_punycode"] is True
    assert suspicious["risk_level"] == "High"
    assert "does not visit" in suspicious["disclaimer"]


def test_shortened_ip_and_suspicious_path_indicators_are_reported():
    shortened = analyze_url("https://bit.ly/a")
    ip_address = analyze_url("https://192.0.2.1/login")

    assert shortened["is_shortened"] is True
    assert shortened["risk_level"] == "Moderate"
    assert ip_address["is_ip_hostname"] is True
    assert ip_address["risk_level"] == "High"


def test_file_hash_and_comparison_routes_and_usage_are_database_derived(client, create_user, app):
    user = create_user()
    login(client)
    original = b"same content"

    hashed = client.post(
        "/tools/hash-generator",
        data={"file": (io.BytesIO(original), "original.txt")},
        content_type="multipart/form-data",
    )
    compared = client.post(
        "/tools/file-comparator",
        data={
            "original": (io.BytesIO(original), "original.txt"),
            "comparison": (io.BytesIO(original), "copy.txt"),
        },
        content_type="multipart/form-data",
    )

    assert hashed.status_code == 200
    assert hashed.json["sha256"] == hashlib.sha256(original).hexdigest()
    assert hashed.json["size"] == len(original)
    assert compared.status_code == 200
    assert compared.json["match"] is True
    different = client.post(
        "/tools/file-comparator",
        data={
            "original": (io.BytesIO(b"original"), "original.txt"),
            "comparison": (io.BytesIO(b"modified"), "modified.txt"),
        },
        content_type="multipart/form-data",
    )
    assert different.status_code == 200
    assert different.json["match"] is False
    with app.app_context():
        events = db.session.scalars(
            select(Activity).where(Activity.user_id == user.id)
        ).all()
        assert [event.activity_type for event in events].count("file_hashed") == 1
        assert [event.activity_type for event in events].count("files_compared") == 2


def test_url_analysis_route_does_not_store_submitted_url(client, create_user, app):
    user = create_user()
    login(client)
    private_url = "https://private.example/path?token=not-stored"

    response = client.post("/tools/url-analyzer", data={"url": private_url})

    assert response.status_code == 200
    assert response.json["uses_https"] is True
    with app.app_context():
        activity = db.session.scalar(
            select(Activity).where(
                Activity.user_id == user.id,
                Activity.activity_type == "url_analyzed",
            )
        )
        assert activity.description == "Analyzed URL indicators"
        assert private_url not in activity.description


def test_hash_report_downloads_csv_and_readable_text(client, create_user):
    create_user()
    login(client)
    csv_response = client.post(
        "/reports/hash",
        data={"file": (io.BytesIO(b"report data"), "report.txt"), "format": "csv"},
        content_type="multipart/form-data",
    )
    text_response = client.post(
        "/reports/hash",
        data={"file": (io.BytesIO(b"report data"), "report.txt"), "format": "txt"},
        content_type="multipart/form-data",
    )

    assert csv_response.status_code == 200
    assert csv_response.mimetype == "text/csv"
    assert b"SHA-256" in csv_response.data
    assert csv_response.headers["Cache-Control"] == "no-store"
    assert text_response.status_code == 200
    assert text_response.mimetype == "text/plain"
    assert b"SHA-256 file hash report" in text_response.data


def test_comparison_and_url_report_downloads(client, create_user):
    create_user()
    login(client)

    comparison = client.post(
        "/reports/comparison",
        data={
            "original": (io.BytesIO(b"one"), "one.txt"),
            "comparison": (io.BytesIO(b"two"), "two.txt"),
            "format": "txt",
        },
        content_type="multipart/form-data",
    )
    url_report = client.post(
        "/reports/url",
        data={"url": "http://example.com/login", "format": "csv"},
    )

    assert comparison.status_code == 200
    assert b"Content hashes differ" in comparison.data
    assert url_report.status_code == 200
    assert url_report.mimetype == "text/csv"
    assert b"HTTP rather than encrypted HTTPS" in url_report.data


def test_upload_limit_is_enforced_by_tool_route(client, create_user, app):
    create_user()
    login(client)
    app.config["MAX_UPLOAD_BYTES"] = 8

    response = client.post(
        "/tools/hash-generator",
        data={"file": (io.BytesIO(b"012345678"), "large.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 413
    assert b"16 MiB or smaller" in response.data


def test_authenticated_tool_pages_render(client, create_user):
    create_user()
    login(client)

    for path in (
        "/tools/hash-generator",
        "/tools/file-comparator",
        "/tools/url-analyzer",
        "/reports/",
    ):
        response = client.get(path)
        assert response.status_code == 200


def test_reports_do_not_treat_csv_formula_values_as_formulas():
    activity = Activity(
        user_id=1,
        activity_type="login",
        description="=HYPERLINK(\"https://example.invalid\")",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    report, _ = build_activity_report([activity], "csv")
    rows = list(csv.reader(io.StringIO(report)))

    assert rows[1][2].startswith("'=")


def test_new_security_tools_and_reports_require_authentication(client):
    for path in (
        "/tools/hash-generator",
        "/tools/file-comparator",
        "/tools/url-analyzer",
        "/activity/",
        "/reports/",
    ):
        response = client.get(path)
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]

    upload = client.post("/reports/hash", data={"file": (io.BytesIO(b"data"), "x.txt")})
    assert upload.status_code == 302