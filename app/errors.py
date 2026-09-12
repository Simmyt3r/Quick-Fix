from flask import flash, redirect, request, url_for
from flask_wtf.csrf import CSRFError


def register_error_handlers(app):
    @app.errorhandler(CSRFError)
    def handle_csrf_error(_e):
        flash("Your session expired — please try again.", "error")
        return redirect(request.referrer or url_for("main.index"))

    @app.errorhandler(429)
    def handle_rate_limit(_e):
        flash("Too many attempts — please wait a bit and try again.", "error")
        return redirect(request.referrer or url_for("main.index"))
