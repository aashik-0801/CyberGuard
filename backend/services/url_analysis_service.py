import ipaddress
import re
from urllib.parse import urlsplit


MAX_URL_LENGTH = 2048
SHORTENER_HOSTS = {
    "bit.ly",
    "buff.ly",
    "is.gd",
    "ow.ly",
    "rebrand.ly",
    "shorturl.at",
    "t.co",
    "tinyurl.com",
}
SUSPICIOUS_TERMS = re.compile(
    r"(?:account|auth|bank|confirm|login|password|secure|signin|update|verify|wallet)",
    re.IGNORECASE,
)


def analyze_url(value: str) -> dict[str, str | bool | list[str]]:
    if not isinstance(value, str) or not value or len(value) > MAX_URL_LENGTH:
        raise ValueError("Enter a URL of up to 2,048 characters.")
    if value != value.strip() or any(
        char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value
    ):
        raise ValueError("The URL must not contain whitespace or control characters.")

    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        parsed.port
    except ValueError as error:
        raise ValueError("Enter a valid HTTP or HTTPS URL.") from error

    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.netloc or not hostname:
        raise ValueError("Enter a valid HTTP or HTTPS URL, including its hostname.")

    hostname = hostname.rstrip(".").lower()
    if not hostname:
        raise ValueError("Enter a valid HTTP or HTTPS URL, including its hostname.")
    try:
        ipaddress.ip_address(hostname)
        is_ip = True
    except ValueError:
        is_ip = False

    has_punycode = any(label.startswith("xn--") for label in hostname.split("."))
    is_shortened = hostname in SHORTENER_HOSTS
    indicators: list[str] = []
    recommendations: list[str] = []

    if scheme == "http":
        indicators.append("This URL uses HTTP rather than encrypted HTTPS.")
        recommendations.append("Avoid entering sensitive information on an HTTP site.")
    if is_ip:
        indicators.append("The hostname is an IP address rather than a domain name.")
        recommendations.append("Verify the destination independently before opening it.")
    if has_punycode:
        indicators.append("The hostname contains an internationalized punycode label.")
        recommendations.append("Check the displayed domain carefully for look-alike characters.")
    if is_shortened:
        indicators.append("This hostname belongs to a recognizable URL-shortening service.")
        recommendations.append("Use a trusted preview or independently verify the final destination.")
    if parsed.username is not None or parsed.password is not None or "@" in parsed.netloc:
        indicators.append("The URL contains user information before its hostname.")
        recommendations.append("Do not use links that obscure their intended destination.")

    if len(hostname.split(".")) > 4:
        indicators.append("The hostname has an unusually large number of subdomain labels.")
        recommendations.append("Read the registered domain from right to left before trusting it.")

    target_text = f"{hostname}{parsed.path}?{parsed.query}".lower()
    if SUSPICIOUS_TERMS.search(target_text):
        indicators.append("The hostname or path includes terms commonly used in account prompts.")
        recommendations.append("Navigate to the service directly instead of following an unexpected link.")
    if re.search(r"%2f|%5c|%40|%2e", target_text, re.IGNORECASE):
        indicators.append("The URL includes encoded separators or punctuation.")
        recommendations.append("Avoid links with unexpected encoded characters.")

    risk_level = "Low"
    if is_ip or has_punycode or "@" in parsed.netloc:
        risk_level = "High"
    elif len(indicators) >= 2 or is_shortened:
        risk_level = "Moderate"

    if not recommendations:
        recommendations.append("Confirm the domain and context before sharing information.")

    return {
        "url": value,
        "scheme": scheme,
        "hostname": hostname,
        "uses_https": scheme == "https",
        "is_ip_hostname": is_ip,
        "has_punycode": has_punycode,
        "is_shortened": is_shortened,
        "risk_level": risk_level,
        "indicators": indicators,
        "recommendations": recommendations,
        "disclaimer": (
            "This transparent heuristic does not visit the URL and cannot determine whether "
            "a site is safe, malicious, or authentic."
        ),
    }