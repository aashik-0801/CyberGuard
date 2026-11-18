import re

import pytest

from backend.services.password_generator import generate_password


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
