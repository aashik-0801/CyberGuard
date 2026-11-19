from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from backend.extensions import limiter
from backend.services.activity import record_activity
from backend.services.file_comparison_service import compare_streams
from backend.services.hash_service import FileTooLargeError, hash_stream
from backend.services.password_generator import CATEGORIES, generate_password
from backend.services.url_analysis_service import analyze_url

tools_bp = Blueprint("tools", __name__, url_prefix="/tools")


@tools_bp.get("/password-checker")
@login_required
def password_checker():
    return render_template("tools/password_checker.html")


@tools_bp.post("/password-checker/used")
@login_required
@limiter.limit("30 per minute")
def password_checker_used():
    record_activity("password_checker", "Used the local password strength checker", current_user.id)
    return ("", 204)


@tools_bp.get("/password-generator")
@login_required
def password_generator():
    return render_template("tools/password_generator.html")


@tools_bp.post("/password-generator")
@login_required
@limiter.limit("20 per minute")
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


@tools_bp.route("/hash-generator", methods=["GET", "POST"])
@login_required
@limiter.limit("10 per minute")
def hash_generator():
    if request.method == "GET":
        return render_template("tools/hash_generator.html")
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return jsonify(error="Choose a file to hash."), 400
    try:
        digest, size = hash_stream(upload.stream, current_app.config["MAX_UPLOAD_BYTES"])
    except FileTooLargeError as error:
        return jsonify(error=str(error)), 413
    record_activity("file_hashed", "Generated a SHA-256 file hash", current_user.id)
    return jsonify(filename=secure_filename(upload.filename) or "uploaded-file", size=size, sha256=digest)


@tools_bp.route("/file-comparator", methods=["GET", "POST"])
@login_required
@limiter.limit("10 per minute")
def file_comparator():
    if request.method == "GET":
        return render_template("tools/file_comparator.html")
    original = request.files.get("original")
    comparison = request.files.get("comparison")
    if original is None or not original.filename or comparison is None or not comparison.filename:
        return jsonify(error="Choose both files to compare."), 400
    try:
        result = compare_streams(
            original.stream,
            comparison.stream,
            current_app.config["MAX_UPLOAD_BYTES"],
        )
    except FileTooLargeError as error:
        return jsonify(error=str(error)), 413
    record_activity("files_compared", "Compared two files using SHA-256", current_user.id)
    return jsonify(
        original_filename=secure_filename(original.filename) or "uploaded-file",
        comparison_filename=secure_filename(comparison.filename) or "uploaded-file",
        **result,
    )


@tools_bp.route("/url-analyzer", methods=["GET", "POST"])
@login_required
@limiter.limit("30 per minute")
def url_analyzer():
    if request.method == "GET":
        return render_template("tools/url_analyzer.html")
    data = request.get_json(silent=True)
    value = data.get("url") if isinstance(data, dict) else request.form.get("url")
    try:
        result = analyze_url(value)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    record_activity("url_analyzed", "Analyzed URL indicators", current_user.id)
    return jsonify(result)
