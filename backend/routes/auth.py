from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from urllib.parse import urlsplit

from backend.extensions import db, limiter
from backend.forms import LoginForm, RegistrationForm
from backend.models import User
from backend.services.activity import record_activity

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        username = form.username.data.strip()
        duplicate = db.session.scalar(
            select(User).where((User.email == email) | (User.username == username))
        )
        if duplicate:
            flash("An account with that email or username already exists.", "error")
            return render_template("auth/register.html", form=form), 409

        user = User(username=username, email=email)
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("An account with that email or username already exists.", "error")
            return render_template("auth/register.html", form=form), 409
        flash("Your account is ready. Sign in to continue.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = db.session.scalar(select(User).where(User.email == email))
        if user is not None and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data, fresh=True)
            record_activity("login", "Successful sign in", user.id)
            target = request.args.get("next")
            parsed_target = urlsplit(target or "")
            if (
                target
                and target.startswith("/")
                and not target.startswith("//")
                and "\\" not in target
                and not parsed_target.scheme
                and not parsed_target.netloc
            ):
                return redirect(target)
            return redirect(url_for("dashboard.index"))

        record_activity(
            "failed_login",
            "Unsuccessful sign-in attempt",
            user.id if user is not None else None,
        )
        flash("The email or password was not recognized.", "error")

    return render_template("auth/login.html", form=form), 200


@auth_bp.post("/logout")
@login_required
def logout():
    record_activity("logout", "Signed out", current_user.id)
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("main.landing"))
