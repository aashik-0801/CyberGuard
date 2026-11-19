from flask import Blueprint, render_template
from flask_login import login_required

from backend.services.network_service import collect_network_information


network_bp = Blueprint("network", __name__, url_prefix="/network")


@network_bp.get("/")
@login_required
def index():
    return render_template("network/index.html", network=collect_network_information())
