import secrets
import string


CATEGORIES = {
    "uppercase": string.ascii_uppercase,
    "lowercase": string.ascii_lowercase,
    "numbers": string.digits,
    "symbols": "!@#$%^&*()-_=+[]{};:,.?/|~",
}


def generate_password(length: int, selected_categories: list[str]) -> str:
    if not 8 <= length <= 64:
        raise ValueError("Choose a length from 8 to 64 characters.")

    pools = [CATEGORIES[name] for name in selected_categories if name in CATEGORIES]
    if not pools:
        raise ValueError("Select at least one character type.")
    if length < len(pools):
        raise ValueError("Password length must fit every selected character type.")

    characters = [secrets.choice(pool) for pool in pools]
    alphabet = "".join(pools)
    characters.extend(secrets.choice(alphabet) for _ in range(length - len(characters)))
    secrets.SystemRandom().shuffle(characters)
    return "".join(characters)
