import os

from flask import Flask

from app.extensions import csrf, db, limiter, login_manager, migrate


def create_app():
    """Application factory for QuickFix Nearby."""
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    os.makedirs(app.instance_path, exist_ok=True)
    default_db_uri = "sqlite:///" + os.path.join(app.instance_path, "quickfix.db")
    db_url = os.environ.get("DATABASE_URL", default_db_uri)
    # Some providers (Heroku-style) hand out "postgres://"; SQLAlchemy/psycopg2 need "postgresql://".
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to view that page."
    login_manager.login_message_category = "error"

    csrf.init_app(app)
    limiter.init_app(app)

    from app import models  # noqa: F401 — register models before Migrate/db touch anything

    migrate.init_app(app, db)

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    from app.cli import create_admin

    app.cli.add_command(create_admin)

    from app.security import register_security_headers
    from app.errors import register_error_handlers

    register_security_headers(app)
    register_error_handlers(app)

    return app
