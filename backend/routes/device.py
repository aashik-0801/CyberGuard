from flask import Blueprint, render_template
from flask_login import login_required

from backend.services.device_service import collect_device_information


device_bp = Blueprint("device", __name__, url_prefix="/device")


@device_bp.get("/")
@login_required
def index():
    return render_template("device/index.html", device=collect_device_information())
