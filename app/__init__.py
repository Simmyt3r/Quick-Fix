import os
from datetime import datetime, timezone

from flask import Flask

from app.extensions import csrf, db, limiter, login_manager, migrate, oauth


def create_app():
    """Application factory for QuickFix Nearby."""
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        # Some providers (Heroku-style) hand out "postgres://"; SQLAlchemy/psycopg2 need "postgresql://".
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
    elif os.environ.get("VERCEL"):
        # Vercel's serverless functions have a read-only filesystem (aside from
        # /tmp), so there's no SQLite fallback to reach for here — fail with a
        # clear message instead of a cryptic filesystem-permission crash.
        raise RuntimeError(
            "DATABASE_URL is not set. This app has no writable filesystem to "
            "fall back to on Vercel, so a real Postgres connection string is "
            "required — set DATABASE_URL in the project's Environment "
            "Variables (e.g. your Neon connection string) and redeploy."
        )
    else:
        os.makedirs(app.instance_path, exist_ok=True)
        db_url = "sqlite:///" + os.path.join(app.instance_path, "quickfix.db")

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB — mainly for avatar uploads

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to view that page."
    login_manager.login_message_category = "error"

    csrf.init_app(app)
    limiter.init_app(app)

    oauth.init_app(app)
    google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
    google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    app.config["GOOGLE_OAUTH_ENABLED"] = bool(google_client_id and google_client_secret)
    if app.config["GOOGLE_OAUTH_ENABLED"]:
        oauth.register(
            name="google",
            client_id=google_client_id,
            client_secret=google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    @app.context_processor
    def inject_google_oauth_flag():
        # So templates can hide the "Continue with Google" button when it's not configured,
        # instead of linking to a route that would just flash an error.
        return {"google_oauth_enabled": app.config["GOOGLE_OAUTH_ENABLED"]}

    @app.context_processor
    def inject_current_year():
        # Keeps the footer copyright year correct without a redeploy every January.
        return {"current_year": datetime.now(timezone.utc).year}

    from app.uploads import init_cloudinary

    init_cloudinary(app)

    from app.mail import init_mail

    init_mail(app)

    from app import models  # noqa: F401 — register models before Migrate/db touch anything

    migrate.init_app(app, db)

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.requests import requests_bp
    from app.routes.profile import profile_bp
    from app.routes.admin import admin_bp
    from app.routes.pros import pros_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(pros_bp)

    from app.cli import create_admin

    app.cli.add_command(create_admin)

    from app.security import register_security_headers
    from app.errors import register_error_handlers

    register_security_headers(app)
    register_error_handlers(app)

    return app
