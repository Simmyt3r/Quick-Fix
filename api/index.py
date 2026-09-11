from app import create_app

# Vercel's Python runtime looks for a WSGI-compatible `app` object here.
app = create_app()
