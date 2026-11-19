import hashlib
from io import BytesIO
import re

import pytest

from backend.services.file_comparison_service import compare_streams
from backend.services.hash_service import FileTooLargeError, hash_stream
from backend.services.password_generator import generate_password
from backend.services.url_analysis_service import analyze_url


def test_hash_stream_handles_empty_and_large_files_in_chunks():
    empty_hash, empty_size = hash_stream(BytesIO(b""), 0)
    content = b"chunked-content" * 100_000
    content_hash, content_size = hash_stream(BytesIO(content), len(content), chunk_size=4096)

    assert empty_hash == hashlib.sha256(b"").hexdigest()
    assert empty_size == 0
    assert content_hash == hashlib.sha256(content).hexdigest()
    assert content_size == len(content)


def test_hash_stream_rejects_data_over_the_configured_limit():
    with pytest.raises(FileTooLargeError):
        hash_stream(BytesIO(b"12345"), 4)


@pytest.mark.parametrize(
    ("original", "comparison", "matches"),
    [(b"same", b"same", True), (b"original", b"changed", False)],
)
def test_compare_streams_hashes_both_files(original, comparison, matches):
    result = compare_streams(BytesIO(original), BytesIO(comparison), 100)

    assert result["original_hash"] == hashlib.sha256(original).hexdigest()
    assert result["comparison_hash"] == hashlib.sha256(comparison).hexdigest()
    assert result["matches"] is matches


@pytest.mark.parametrize("value", ["", "example.com", "javascript:alert(1)", "https://host name/path"])
def test_url_analyzer_rejects_invalid_urls(value):
    with pytest.raises(ValueError):
        analyze_url(value)


def test_url_analyzer_reports_protocol_and_hostname_indicators():
    https_result = analyze_url("https://example.com")
    http_result = analyze_url("http://192.0.2.1/login")
    punycode_result = analyze_url("https://xn--e1afmkfd.example/")
    shortener_result = analyze_url("https://bit.ly/abc")

    assert https_result["is_https"] is True
    assert https_result["risk"] == "Low"
    assert http_result["is_http"] is True
    assert http_result["is_ip"] is True
    assert http_result["risk"] == "Elevated"
    assert punycode_result["is_punycode"] is True
    assert shortener_result["is_shortener"] is True


def test_url_analyzer_rejects_malformed_port():
    with pytest.raises(ValueError):
        analyze_url("https://example.com:99999")


@pytest.mark.parametrize(
    ("length", "categories"),
    [
        (8, ["uppercase"]),
        (12, ["lowercase", "numbers"]),
        (64, ["uppercase", "lowercase", "numbers", "symbols"]),
    ],
)
def test_generator_respects_length_and_selected_categories(length, categories):
    password = generate_password(length, categories)

    assert len(password) == length
    patterns = {
        "uppercase": r"[A-Z]",
        "lowercase": r"[a-z]",
        "numbers": r"[0-9]",
        "symbols": r"[!@#$%^&*()\-_=+\[\]{};:,.?/|~]",
    }
    for category in categories:
        assert re.search(patterns[category], password)


@pytest.mark.parametrize(
    ("length", "categories"),
    [
        (7, ["lowercase"]),
        (65, ["lowercase"]),
        (8, []),
    ],
)
def test_generator_rejects_invalid_settings(length, categories):
    with pytest.raises(ValueError):
        generate_password(length, categories)
