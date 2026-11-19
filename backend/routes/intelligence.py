from datetime import date

from flask import Blueprint, abort, jsonify, render_template, request
from flask_login import current_user, login_required

from backend.services.analytics_service import get_analytics
from backend.services.recommendation_service import generate_recommendations


intelligence_bp = Blueprint("intelligence", __name__, url_prefix="/intelligence")


def _parse_filters():
    date_from = None
    date_to = None
    try:
        if request.args.get("date_from"):
            date_from = date.fromisoformat(request.args["date_from"])
        if request.args.get("date_to"):
            date_to = date.fromisoformat(request.args["date_to"])
    except ValueError:
        abort(400, description="Use valid YYYY-MM-DD dates.")
    if date_from and date_to and date_from > date_to:
        abort(400, description="The start date must not be after the end date.")
    return date_from, date_to


@intelligence_bp.get("/recommendations")
@login_required
def recommendations():
    return render_template(
        "intelligence/recommendations.html",
        recommendations=generate_recommendations(current_user.id),
    )


@intelligence_bp.get("/analytics")
@login_required
def analytics():
    date_from, date_to = _parse_filters()
    return render_template(
        "intelligence/analytics.html",
        filters={
            "date_from": date_from.isoformat() if date_from else "",
            "date_to": date_to.isoformat() if date_to else "",
        },
    )


@intelligence_bp.get("/analytics.json")
@login_required
def analytics_json():
    date_from, date_to = _parse_filters()
    return jsonify(get_analytics(current_user.id, date_from, date_to))
