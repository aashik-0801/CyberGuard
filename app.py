import logging
import os

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_wtf.csrf import CSRFError

from backend.extensions import csrf, db, limiter, login_manager
from backend.models import User

load_dotenv()


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")
    app.config.from_object("config.Config")
    if test_config:
        app.config.update(test_config)
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be configured in the environment before starting CyberGuard.")

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Sign in to access your security workspace."
    login_manager.login_message_category = "error"

    from backend.routes.auth import auth_bp
    from backend.routes.dashboard import dashboard_bp
    from backend.routes.main import main_bp
    from backend.routes.profile import profile_bp
    from backend.routes.tools import tools_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(tools_bp)

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        if not user_id.isdecimal():
            return None
        return db.session.get(User, int(user_id))

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
            "font-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'",
        )
        return response

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        app.logger.warning("Rejected a request with an invalid or expired CSRF token.")
        return render_template("error.html", message="Your session expired. Refresh the page and try again."), 400

    @app.errorhandler(429)
    def handle_rate_limit(error):
        return render_template("error.html", message="Too many sign-in attempts. Please wait a minute and try again."), 429

    @app.errorhandler(500)
    def handle_server_error(error):
        db.session.rollback()
        app.logger.exception("Unhandled application error", exc_info=error)
        return render_template("error.html", message="Something went wrong. Please try again later."), 500

    with app.app_context():
        db.create_all()

    if not app.testing:
        logging.basicConfig(level=logging.INFO)
    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
