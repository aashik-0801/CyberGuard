import io
from datetime import date

from flask import Blueprint, abort, current_app, jsonify, render_template, request, send_file
from flask_login import current_user, login_required
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from backend.extensions import db, limiter
from backend.services.activity import activity_query, record_activity
from backend.services.file_comparison_service import compare_streams
from backend.services.hash_service import FileTooLargeError, hash_stream
from backend.services.report_service import build_activity_report, build_report
from backend.services.url_analysis_service import analyze_url
from backend.services.device_service import collect_device_information
from backend.services.network_service import collect_network_information
from backend.services.recommendation_service import generate_recommendations
from backend.services.security_report_service import (
    build_security_report_csv,
    build_security_report_html,
)


reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def _download_report(title: str, rows: list[tuple[str, object]], file_format: str, filename: str):
    if file_format not in {"csv", "txt"}:
        return jsonify(error="Choose CSV or text format."), 400
    try:
        content, mimetype = build_report(title, rows, file_format)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    response = send_file(
        io.BytesIO(content.encode("utf-8")),
        mimetype=mimetype,
        as_attachment=True,
        download_name=f"{filename}.{file_format}",
        max_age=0,
    )
    response.headers["Cache-Control"] = "no-store"
    return response


def _required_upload(name: str) -> FileStorage | None:
    upload = request.files.get(name)
    return upload if upload is not None and upload.filename else None


def _filtered_activities():
    from backend.routes.activity import ACTIVITY_CATEGORIES

    search = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    if len(search) > 100 or category not in ("", *ACTIVITY_CATEGORIES):
        return None, (jsonify(error="The requested activity filters are invalid."), 400)
    try:
        date_from = date.fromisoformat(request.args["date_from"]) if request.args.get("date_from") else None
        date_to = date.fromisoformat(request.args["date_to"]) if request.args.get("date_to") else None
    except ValueError:
        return None, (jsonify(error="Use a valid YYYY-MM-DD date."), 400)
    if date_from and date_to and date_from > date_to:
        return None, (jsonify(error="The start date must not be after the end date."), 400)
    return activity_query(current_user.id, search, category, date_from, date_to), None


@reports_bp.get("/")
@login_required
def index():
    return render_template("reports/index.html")


@reports_bp.post("/hash")
@login_required
@limiter.limit("10 per minute")
def hash_report():
    upload = _required_upload("file")
    if upload is None:
        return jsonify(error="Choose a file to hash."), 400
    file_format = request.form.get("format", "txt")
    if file_format not in {"csv", "txt"}:
        return jsonify(error="Choose CSV or text format."), 400
    try:
        digest, size = hash_stream(upload.stream, current_app.config["MAX_UPLOAD_BYTES"])
    except FileTooLargeError as error:
        return jsonify(error=str(error)), 413
    record_activity("file_hashed", "Generated a SHA-256 file hash", current_user.id)
    rows = [
        ("File name", secure_filename(upload.filename) or "uploaded-file"),
        ("File size (bytes)", size),
        ("Algorithm", "SHA-256"),
        ("SHA-256", digest),
    ]
    return _download_report(
        "CyberGuard SHA-256 file hash report",
        rows,
        file_format,
        "cyberguard-hash-report",
    )


@reports_bp.post("/comparison")
@login_required
@limiter.limit("10 per minute")
def comparison_report():
    original = _required_upload("original")
    comparison = _required_upload("comparison")
    if original is None or comparison is None:
        return jsonify(error="Choose both files to compare."), 400
    file_format = request.form.get("format", "txt")
    if file_format not in {"csv", "txt"}:
        return jsonify(error="Choose CSV or text format."), 400
    try:
        result = compare_streams(
            original.stream,
            comparison.stream,
            current_app.config["MAX_UPLOAD_BYTES"],
        )
    except FileTooLargeError as error:
        return jsonify(error=str(error)), 413
    record_activity("files_compared", "Compared two files using SHA-256", current_user.id)
    match = bool(result["match"])
    rows = [
        ("Original file", secure_filename(original.filename) or "uploaded-file"),
        ("Original size (bytes)", result["original_size"]),
        ("Original SHA-256", result["original_hash"]),
        ("Comparison file", secure_filename(comparison.filename) or "uploaded-file"),
        ("Comparison size (bytes)", result["comparison_size"]),
        ("Comparison SHA-256", result["comparison_hash"]),
        ("Result", "Content hashes match" if match else "Content hashes differ"),
        ("Limitation", "Matching hashes indicate content equality only; they do not prove authenticity or safety."),
    ]
    return _download_report(
        "CyberGuard file comparison report",
        rows,
        file_format,
        "cyberguard-file-comparison-report",
    )


@reports_bp.post("/url")
@login_required
@limiter.limit("30 per minute")
def url_report():
    file_format = request.form.get("format", "txt")
    if file_format not in {"csv", "txt"}:
        return jsonify(error="Choose CSV or text format."), 400
    try:
        result = analyze_url(request.form.get("url", ""))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    record_activity("url_analyzed", "Analyzed URL indicators", current_user.id)
    rows = [
        ("URL", result["url"]),
        ("Hostname", result["hostname"]),
        ("HTTPS", result["uses_https"]),
        ("IP hostname", result["is_ip_hostname"]),
        ("Punycode", result["has_punycode"]),
        ("Recognizable shortener", result["is_shortened"]),
        ("Heuristic risk indicator", result["risk_level"]),
        ("Indicators", "; ".join(result["indicators"]) or "None detected"),
        ("Recommendations", "; ".join(result["recommendations"])),
        ("Limitations", result["disclaimer"]),
    ]
    return _download_report(
        "CyberGuard URL analysis report",
        rows,
        file_format,
        "cyberguard-url-analysis-report",
    )


@reports_bp.get("/activity/<file_format>")
@login_required
@limiter.limit("20 per minute")
def activity_report(file_format: str):
    if file_format not in {"csv", "txt"}:
        abort(404)
    query, error_response = _filtered_activities()
    if error_response:
        return error_response
    activities = db.session.scalars(query).all()
    content, mimetype = build_activity_report(activities, file_format)
    response = send_file(
        io.BytesIO(content.encode("utf-8")),
        mimetype=mimetype,
        as_attachment=True,
        download_name=f"cyberguard-activity.{file_format}",
        max_age=0,
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@reports_bp.get("/security/<file_format>")
@login_required
@limiter.limit("10 per minute")
def security_report(file_format: str):
    if file_format not in {"csv", "html"}:
        abort(404)
    device = collect_device_information()
    network = collect_network_information()
    recommendations = generate_recommendations(current_user.id)
    if file_format == "csv":
        content = build_security_report_csv(
            current_user.id,
            current_user.username,
            device,
            network,
            recommendations,
        )
        response = send_file(
            io.BytesIO(content),
            mimetype="text/csv",
            as_attachment=True,
            download_name="cyberguard-security-report.csv",
            max_age=0,
        )
    else:
        content = build_security_report_html(
            current_user.id,
            current_user.username,
            device,
            network,
            recommendations,
        )
        response = send_file(
            io.BytesIO(content.encode("utf-8")),
            mimetype="text/html",
            as_attachment=True,
            download_name="cyberguard-security-report.html",
            max_age=0,
        )
    response.headers["Cache-Control"] = "no-store"
    return response