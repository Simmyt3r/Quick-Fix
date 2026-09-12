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
    """Create an admin user: flask create-admin you@example.com yourpassword"""
    if User.query.filter_by(email=email).first():
        click.echo(f"A user with {email} already exists.")
        return

    user = User(name=name, email=email, role="admin", verified=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Admin created: {email}")
