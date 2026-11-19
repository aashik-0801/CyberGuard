from sqlalchemy import func, select

from backend.extensions import db
from backend.models import Activity


def _count(user_id: int, activity_types: tuple[str, ...]) -> int:
    return db.session.scalar(
        select(func.count(Activity.id)).where(
            Activity.user_id == user_id,
            Activity.activity_type.in_(activity_types),
        )
    ) or 0


def generate_recommendations(user_id: int) -> list[dict[str, str]]:
    failed_logins = _count(user_id, ("failed_login",))
    url_analyses = _count(user_id, ("url_analyzed",))
    hash_operations = _count(user_id, ("file_hashed", "files_compared"))

    recommendations: list[dict[str, str]] = []
    if failed_logins:
        recommendations.append({
            "severity": "Review",
            "classification": "Verified application finding",
            "title": "Review recent failed sign-in attempts",
            "reason": f"{failed_logins} failed sign-in event(s) are recorded for this account.",
        })
    if url_analyses:
        recommendations.append({
            "severity": "Caution",
            "classification": "Evidence-based informational recommendation",
            "title": "Review HTTP-only URL indicators carefully",
            "reason": f"{url_analyses} URL analysis event(s) show this tool has been used.",
        })
    if hash_operations:
        recommendations.append({
            "severity": "Caution",
            "classification": "Evidence-based informational recommendation",
            "title": "Verify file provenance as well as hashes",
            "reason": f"{hash_operations} hash or comparison event(s) are recorded. A matching hash proves content equality, not authenticity.",
        })

    recommendations.extend([
        {
            "severity": "Best practice",
            "classification": "General informational recommendation",
            "title": "Use a unique password for each account",
            "reason": "This is a general account-security practice and does not claim that a password is weak or reused.",
        },
        {
            "severity": "Deployment",
            "classification": "General configuration recommendation",
            "title": "Enable HTTPS in a production deployment",
            "reason": "HTTPS protects browser-to-server traffic, but CyberGuard does not claim to verify a production deployment.",
        },
        {
            "severity": "Maintenance",
            "classification": "General informational recommendation",
            "title": "Keep application dependencies updated",
            "reason": "CyberGuard does not perform dependency or vulnerability scanning.",
        },
    ])
    return recommendations