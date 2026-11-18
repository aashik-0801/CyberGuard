from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.extensions import db
from backend.forms import ProfileForm
from backend.models import User
from backend.services.activity import record_activity

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = ProfileForm(username=current_user.username)
    if form.validate_on_submit():
        username = form.username.data.strip()
        duplicate = db.session.scalar(
            select(User).where(User.username == username, User.id != current_user.id)
        )
        if duplicate:
            form.username.errors.append("That username is already in use.")
        elif username != current_user.username:
            current_user.username = username
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                form.username.errors.append("That username is already in use.")
            else:
                record_activity("profile_updated", "Updated profile username", current_user.id)
                flash("Your profile has been updated.", "success")
                return redirect(url_for("profile.index"))
        else:
            flash("Your profile is up to date.", "success")
            return redirect(url_for("profile.index"))

    return render_template("profile/index.html", form=form)
