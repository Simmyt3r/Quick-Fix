"""
Shared input-validation helpers.

The project's forms have always done *some* validation ad hoc — .strip(),
checking against a set of valid choices, length checks on a few fields —
but it was inconsistent across routes, and several free-text fields had
no length cap at all before hitting the database. Postgres raises a hard
error on a value that overflows a String(n) column (SQLite just silently
truncates, which is its own quiet bug), and an unbounded field is also a
DoS vector — someone can POST a multi-megabyte string to a Text field
with no length limit at all.

These are deliberately simple functions, not a form library — the app
doesn't use WTForms for its data forms (only Flask-WTF's CSRF piece), and
introducing one now would be a much bigger, higher-risk change than the
validation gap itself justifies.
"""
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_str(value, max_length, required=False):
    """Strip and cap a string field. Returns None if required and empty."""
    value = (value or "").strip()
    if required and not value:
        return None
    return value[:max_length]


def valid_email(value):
    value = (value or "").strip().lower()
    if not value or len(value) > 120 or not EMAIL_RE.match(value):
        return None
    return value


def valid_int(value, min_value=None, max_value=None):
    """Parse an int from user input (form/query string), or None if it
    isn't one — never raises, so callers don't need their own try/except
    around every int(request.form.get(...))."""
    if value is None:
        return None
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    if min_value is not None and parsed < min_value:
        return None
    if max_value is not None and parsed > max_value:
        return None
    return parsed


def valid_choice(value, choices, default=None):
    """Return value if it's one of choices, else default."""
    return value if value in choices else default
