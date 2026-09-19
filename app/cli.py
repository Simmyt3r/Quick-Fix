import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import User


@click.command("create-admin")
@click.argument("email")
@click.argument("password")
@click.option("--name", default="Admin")
@with_appcontext
def create_admin(email, password, name):
    """Create an admin user, or promote an existing account to admin:
    flask create-admin you@example.com yourpassword

    If the email already belongs to an account, that account is promoted
    to admin and left otherwise untouched — the password argument is
    ignored in that case, since silently overwriting someone's existing
    password would be a bigger surprise than requiring a separate
    password-reset step. Only a brand-new account gets the given password.
    """
    existing = User.query.filter_by(email=email).first()
    if existing:
        if existing.role == "admin":
            click.echo(f"{email} is already an admin — nothing to do.")
        else:
            existing.role = "admin"
            existing.verified = True
            db.session.commit()
            click.echo(f"Promoted existing account to admin: {email} (password unchanged)")
        return

    user = User(name=name, email=email, role="admin", verified=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Admin created: {email}")
