from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from backend.services.activity import record_activity
from backend.services.password_generator import CATEGORIES, generate_password

tools_bp = Blueprint("tools", __name__, url_prefix="/tools")


@tools_bp.get("/password-checker")
@login_required
def password_checker():
    return render_template("tools/password_checker.html")


@tools_bp.post("/password-checker/used")
@login_required
def password_checker_used():
    record_activity("password_checker", "Used the local password strength checker", current_user.id)
    return ("", 204)


@tools_bp.get("/password-generator")
@login_required
def password_generator():
    return render_template("tools/password_generator.html")


@tools_bp.post("/password-generator")
@login_required
def generate_password_api():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Send generator settings as JSON."), 400

    length = data.get("length")
    if type(length) is not int:
        return jsonify(error="Length must be a whole number from 8 to 64."), 400

    categories = data.get("categories")
    if not isinstance(categories, dict) or any(
        type(value) is not bool for value in categories.values()
    ):
        return jsonify(error="Choose one or more valid character types."), 400

    unknown_categories = set(categories) - set(CATEGORIES)
    if unknown_categories:
        return jsonify(error="One or more character types are invalid."), 400

    selected = [name for name, enabled in categories.items() if enabled]
    try:
        password = generate_password(length, selected)
    except ValueError as error:
        return jsonify(error=str(error)), 400

    record_activity("password_generated", "Generated a password", current_user.id)
    return jsonify(password=password)
