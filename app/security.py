from flask import request

CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; "
    "img-src 'self' data: https://res.cloudinary.com; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)


def register_security_headers(app):
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = CSP
        # Only sent over HTTPS — sending it over plain HTTP locally could be
        # misleading and some browsers ignore it there anyway.
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"

        # The service worker script lives under /static/ but needs to
        # control the whole site ('/'), so its scope has to be widened
        # explicitly here — browsers refuse to register it at scope '/'
        # otherwise (SecurityError, script served outside its max scope).
        # Set from the app itself, not just vercel.json, since Vercel's
        # legacy routes+headers config has been unreliable about actually
        # applying a separately-declared headers block.
        if request.path == "/static/sw.js":
            response.headers["Service-Worker-Allowed"] = "/"

        return response
