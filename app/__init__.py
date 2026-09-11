import os

from flask import Flask


def create_app():
    """Application factory for QuickFix Nearby."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    from app.routes.main import main_bp

    app.register_blueprint(main_bp)

    return app
