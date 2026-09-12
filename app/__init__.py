import os

from flask import Flask

from app.extensions import db, login_manager


def create_app():
    """Application factory for QuickFix Nearby."""
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    os.makedirs(app.instance_path, exist_ok=True)
    default_db_uri = "sqlite:///" + os.path.join(app.instance_path, "quickfix.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", default_db_uri)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to view that page."
    login_manager.login_message_category = "error"

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    from app.cli import create_admin

    app.cli.add_command(create_admin)

    with app.app_context():
        from app import models  # noqa: F401 — register models before create_all

        # TODO(phase 1): replace with Flask-Migrate/Alembic before this ever
        # touches a real Postgres database — create_all() is dev-only.
        db.create_all()

    return app
